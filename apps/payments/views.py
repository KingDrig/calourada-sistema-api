import mercadopago
from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Pagamento
from .serializers import (
    PagamentoSerializer,
    WebhookPayloadSerializer,
    CriarPagamentoSerializer
)
from apps.orders.models import Pedido


class MercadoPagoPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CriarPagamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pedido_id = serializer.validated_data['pedido_id']
        metodo = serializer.validated_data.get('metodo')

        try:
            pedido = Pedido.objects.select_related(
                'usuario', 'evento'
            ).prefetch_related('itens', 'itens__lote').get(
                id=pedido_id,
                usuario=request.user
            )
        except Pedido.DoesNotExist:
            return Response(
                {'detail': 'Pedido não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if pedido.status != Pedido.StatusPedido.APROVADO:
            return Response(
                {'detail': 'Pedido precisa estar APROVADO para realizar o pagamento.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if hasattr(pedido, 'pagamento'):
            pagamento_existente = pedido.pagamento
            if pagamento_existente.status == Pagamento.StatusPagamento.APROVADO:
                return Response(
                    {'detail': 'Este pedido já foi pago.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if pagamento_existente.status == Pagamento.StatusPagamento.PENDENTE and \
               pagamento_existente.preference_id:
                return Response({
                    'message': 'Pagamento já iniciado.',
                    'pagamento': PagamentoSerializer(pagamento_existente).data
                })

        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

        items = []
        for item_pedido in pedido.itens.all():
            items.append({
                "title": f"Ingresso {item_pedido.lote.get_tipo_display()} - {pedido.evento.nome}",
                "quantity": item_pedido.quantidade,
                "unit_price": float(item_pedido.preco_unitario),
                "currency_id": "BRL"
            })

        payer_info = {
            "name": pedido.usuario.first_name or pedido.usuario.username,
            "surname": pedido.usuario.last_name or "",
            "email": pedido.usuario.email
        }

        payment_methods = {
            "excluded_payment_types": [
                {"id": "ticket"},
                {"id": "atm"}
            ],
            "installments": 1
        }

        if metodo == 'CARTAO_CREDITO' or metodo == 'CARTAO_DEBITO':
            payment_methods = {
                "excluded_payment_types": [
                    {"id": "ticket"},
                    {"id": "atm"},
                    {"id": "pix"}
                ],
                "installments": 1
            }

        preference_data = {
            "items": items,
            "payer": payer_info,
            "external_reference": str(pedido.id),
            "notification_url": f"{settings.BASE_URL}/api/payments/webhook/",
            "payment_methods": payment_methods,
            "expires": False
        }

        try:
            preference_response = sdk.preference().create(preference_data)
            
            if preference_response["status"] != 201:
                return Response(
                    {'detail': 'Erro ao criar preferência de pagamento.', 'error': preference_response},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            preference = preference_response["response"]

            pagamento = Pagamento.objects.create(
                pedido=pedido,
                valor=pedido.valor_total,
                preference_id=preference['id'],
                external_reference=str(pedido.id),
                status=Pagamento.StatusPagamento.PENDENTE,
                url_pagamento=preference.get('init_point', '')
            )

            if metodo:
                pagamento.metodo = metodo
                pagamento.save()

            response_data = {
                'pagamento_id': pagamento.id,
                'preference_id': preference['id'],
                'init_point': preference.get('init_point', ''),
                'sandbox_init_point': preference.get('sandbox_init_point', ''),
                'qr_code': preference.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code', ''),
                'qr_code_base64': preference.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code_base64', '')
            }

            if response_data['qr_code_base64']:
                pagamento.codigo_pix = response_data['qr_code_base64']
                pagamento.save()

            return Response({
                'message': 'Preferência de pagamento criada com sucesso.',
                'pagamento': PagamentoSerializer(pagamento).data,
                **response_data
            })

        except Exception as e:
            return Response(
                {'detail': f'Erro ao processar pagamento: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MercadoPagoWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = WebhookPayloadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'status': 'invalid_payload'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        action = data.get('action', '')
        topic = data.get('type', '')

        if topic == 'payment' or action in ['payment.created', 'payment.updated', 'payment.preauthorized']:
            payment_id = data.get('data', {}).get('id')
            
            if not payment_id:
                payment_id = data.get('id')

            if payment_id:
                try:
                    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                    payment_info = sdk.payment().get(payment_id)
                    
                    if payment_info["status"] == 200:
                        payment_data = payment_info["response"]
                        self._process_payment(payment_data)
                        
                except Exception as e:
                    pass

        elif topic == 'merchant_order' or action.startswith('merchant_order'):
            order_id = data.get('data', {}).get('id')
            
            if order_id:
                try:
                    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                    order_info = sdk.merchant_order().get(order_id)
                    
                    if order_info["status"] == 200:
                        order_data = order_info["response"]
                        payments = order_data.get('payments', [])
                        
                        for payment_item in payments:
                            if payment_item['status'] == 'approved':
                                self._process_payment(payment_item)
                                
                except Exception as e:
                    pass

        return Response({'status': 'received'}, status=status.HTTP_200_OK)

    def _process_payment(self, payment_data):
        from apps.tickets.tasks import gerar_ingressos_e_enviar_email

        external_ref = payment_data.get('external_reference')
        payment_status = payment_data.get('status')

        if not external_ref:
            return

        try:
            pedido = Pedido.objects.select_related('pagamento').get(id=external_ref)
        except Pedido.DoesNotExist:
            return

        if not hasattr(pedido, 'pagamento'):
            return

        pagamento = pedido.pagamento

        if payment_status == 'approved':
            if pagamento.status != Pagamento.StatusPagamento.APROVADO:
                pagamento.payment_id = str(payment_data.get('id', ''))
                pagamento.status = Pagamento.StatusPagamento.APROVADO
                pagamento.aprovado_em = timezone.now()
                pagamento.webhook_received_at = timezone.now()
                pagamento.webhook_payload = payment_data
                
                metodo_mapping = {
                    'credit_card': Pagamento.MetodoPagamento.CARTAO_CREDITO,
                    'debit_card': Pagamento.MetodoPagamento.CARTAO_DEBITO,
                    'pix': Pagamento.MetodoPagamento.PIX
                }
                payment_type = payment_data.get('payment_type_id', '').lower()
                pagamento.metodo = metodo_mapping.get(payment_type, '')
                
                pagamento.save()

                pedido.status = Pedido.StatusPedido.PAGO
                pedido.save()

                gerar_ingressos_e_enviar_email.delay(pedido.id)

        elif payment_status in ['rejected', 'cancelled', 'refunded']:
            pagamento.payment_id = str(payment_data.get('id', ''))
            pagamento.status = Pagamento.StatusPagamento.RECUSADO
            pagamento.webhook_received_at = timezone.now()
            pagamento.webhook_payload = payment_data
            pagamento.save()


class PagamentoDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            pagamento = Pagamento.objects.select_related(
                'pedido', 'pedido__usuario', 'pedido__evento'
            ).get(pedido_id=pk)
        except Pagamento.DoesNotExist:
            return Response(
                {'detail': 'Pagamento não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if pagamento.pedido.usuario != request.user and not request.user.is_admin:
            return Response(
                {'detail': 'Você não tem permissão para ver este pagamento.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(PagamentoSerializer(pagamento).data)
