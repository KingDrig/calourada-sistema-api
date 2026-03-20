from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Sum
from apps.core.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.events.models import Lote, Evento
from .models import Pedido, ItemPedido, Documento, ItemVenda, ItemCarrinho
from .serializers import (
    PedidoSerializer, PedidoDetailSerializer,
    CheckoutSerializer, DocumentoSerializer,
    DocumentoUploadSerializer, AdminVerificacaoSerializer,
    ItemVendaSerializer, ItemCarrinhoSerializer
)


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Pedido.objects.select_related(
                'usuario', 'evento', 'documento'
            ).prefetch_related('itens', 'itens__lote').all()
        return Pedido.objects.filter(
            usuario=self.request.user
        ).select_related('evento').prefetch_related('itens', 'itens__lote')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PedidoDetailSerializer
        return PedidoSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminUser()]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        evento_id = serializer.validated_data.get('evento_id')
        itens_data = serializer.validated_data.get('itens', [])
        produtos_data = serializer.validated_data.get('produtos', [])

        if evento_id:
            evento = get_object_or_404(Evento, id=evento_id, ativo=True)

            if evento.ja_ocorreu:
                return Response(
                    {'detail': 'Este evento já ocorreu.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_ingressos_existentes = Pedido.objects.filter(
                usuario=request.user,
                evento=evento,
                status__in=[
                    Pedido.StatusPedido.PENDENTE_VALIDACAO,
                    Pedido.StatusPedido.APROVADO,
                    Pedido.StatusPedido.PAGO
                ]
            ).aggregate(
                total=Sum('itens__quantidade')
            )['total'] or 0

            total_novos = sum(item['quantidade'] for item in itens_data)

            if total_ingressos_existentes + total_novos > 2:
                return Response(
                    {'detail': f'Limite de 2 ingressos por pessoa por evento excedido.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            evento = None

        if produtos_data and not evento:
            pedido = Pedido.objects.create(
                usuario=request.user,
                evento=None,
                status=Pedido.StatusPedido.APROVADO,
                valor_total=0
            )
        elif evento:
            pedido = Pedido.objects.create(
                usuario=request.user,
                evento=evento,
                status=Pedido.StatusPedido.PENDENTE_VALIDACAO,
                valor_total=0
            )
        else:
            return Response(
                {'detail': 'Informe evento ou produtos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valor_total = 0
        requer_documento = False

        if evento_id:
            for item_data in itens_data:
                lote = get_object_or_404(Lote, id=item_data['lote_id'], evento=evento, ativo=True)

                if not lote.esta_disponivel:
                    raise ValueError(f"Lote '{lote.nome}' não está mais disponível.")

                if lote.quantidade_disponivel < item_data['quantidade']:
                    raise ValueError(f"Lote '{lote.nome}' sem estoque.")

                if lote.requer_documento:
                    requer_documento = True

                ItemPedido.objects.create(
                    pedido=pedido,
                    lote=lote,
                    quantidade=item_data['quantidade'],
                    preco_unitario=lote.preco
                )

                valor_total += lote.preco * item_data['quantidade']
                lote.quantidade_disponivel -= item_data['quantidade']
                lote.save()

        for prod_data in produtos_data:
            item_venda = get_object_or_404(ItemVenda, id=prod_data['item_venda_id'], ativo=True)

            if not item_venda.em_estoque:
                raise ValueError(f"'{item_venda.nome}' fora de estoque.")

            if item_venda.quantidade_estoque < prod_data['quantidade']:
                raise ValueError(f"'{item_venda.nome}' possui apenas {item_venda.quantidade_estoque} unidades.")

            ItemPedido.objects.create(
                pedido=pedido,
                lote_id=item_venda.id,
                quantidade=prod_data['quantidade'],
                preco_unitario=item_venda.preco
            )

            valor_total += item_venda.preco * prod_data['quantidade']
            item_venda.quantidade_estoque -= prod_data['quantidade']
            item_venda.save()

        pedido.valor_total = valor_total

        if evento_id and not requer_documento:
            pedido.status = Pedido.StatusPedido.APROVADO

        pedido.save()

        return Response(
            PedidoDetailSerializer(pedido).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancelar(self, request, pk=None):
        pedido = self.get_object()

        if request.user != pedido.usuario and not request.user.is_admin:
            return Response(
                {'detail': 'Você não tem permissão para cancelar este pedido.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if pedido.status == Pedido.StatusPedido.PAGO:
            return Response(
                {'detail': 'Não é possível cancelar um pedido já pago.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for item in pedido.itens.all():
            if hasattr(item, 'lote') and item.lote and hasattr(item.lote, 'quantidade_disponivel'):
                item.lote.quantidade_disponivel += item.quantidade
                item.lote.save()

        pedido.status = Pedido.StatusPedido.CANCELADO
        pedido.save()

        return Response(PedidoDetailSerializer(pedido).data)


class DocumentoUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = DocumentoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pedido_id = request.data.get('pedido_id')
        if not pedido_id:
            return Response(
                {'detail': 'pedido_id é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pedido = get_object_or_404(
            Pedido,
            id=pedido_id,
            usuario=request.user
        )

        if pedido.status != Pedido.StatusPedido.PENDENTE_VALIDACAO:
            return Response(
                {'detail': 'Pedido não está pendente de validação.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not pedido.requer_documento:
            return Response(
                {'detail': 'Este pedido não requer upload de documento.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if hasattr(pedido, 'documento'):
            documento = pedido.documento
            documento.arquivo = serializer.validated_data['arquivo']
            documento.save()
        else:
            documento = serializer.save(pedido=pedido)

        return Response(
            DocumentoSerializer(documento).data,
            status=status.HTTP_201_CREATED
        )


class AdminVerificacaoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.select_related(
        'pedido', 'pedido__usuario'
    ).all()
    serializer_class = DocumentoSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        return queryset

    @transaction.atomic
    def partial_update(self, request, pk=None):
        documento = self.get_object()
        serializer = AdminVerificacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        novo_status = serializer.validated_data['status']
        motivo = serializer.validated_data.get('motivo_rejeicao', '')

        documento.status = novo_status
        documento.verificado = novo_status == 'APROVADO'
        documento.verificado_por = request.user
        from django.utils import timezone
        documento.verificado_em = timezone.now()
        documento.motivo_rejeicao = motivo if novo_status == 'REJEITADO' else ''
        documento.save()

        pedido = documento.pedido
        if novo_status == 'APROVADO':
            pedido.status = Pedido.StatusPedido.APROVADO
            pedido.save()
        else:
            pedido.status = Pedido.StatusPedido.REJEITADO
            pedido.save()
            for item in pedido.itens.all():
                if hasattr(item, 'lote') and item.lote and hasattr(item.lote, 'quantidade_disponivel'):
                    item.lote.quantidade_disponivel += item.quantidade
                    item.lote.save()

        return Response(PedidoDetailSerializer(pedido).data)

    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        docs = self.get_queryset().filter(
            status=Documento.StatusDocumento.PENDENTE
        ).order_by('criado_em')
        return Response(DocumentoSerializer(docs, many=True).data)


class ItemVendaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ItemVenda.objects.filter(ativo=True)
    serializer_class = ItemVendaSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return ItemVenda.objects.filter(ativo=True, quantidade_estoque__gt=0)


class CarrinhoViewSet(viewsets.ModelViewSet):
    serializer_class = ItemCarrinhoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ItemCarrinho.objects.filter(
            usuario=self.request.user
        ).select_related('item_venda')

    def create(self, request, *args, **kwargs):
        item_venda_id = request.data.get('item_venda_id')
        quantidade = request.data.get('quantidade', 1)

        item_venda = get_object_or_404(ItemVenda, id=item_venda_id, ativo=True)

        if not item_venda.em_estoque:
            return Response(
                {'detail': 'Produto fora de estoque.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        carrinho_item, created = ItemCarrinho.objects.get_or_create(
            usuario=request.user,
            item_venda=item_venda,
            defaults={'quantidade': quantidade}
        )

        if not created:
            carrinho_item.quantidade += quantidade
            carrinho_item.save()

        return Response(
            ItemCarrinhoSerializer(carrinho_item).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['delete'])
    def limpar(self, request):
        ItemCarrinho.objects.filter(usuario=request.user).delete()
        return Response({'detail': 'Carrinho limpo.'})
