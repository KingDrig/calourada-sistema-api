from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io
import qrcode
import qrcode.constants
from django.core.files import File


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def gerar_ingressos_e_enviar_email(self, pedido_id):
    from apps.orders.models import Pedido
    from apps.tickets.models import Ingresso

    try:
        pedido = Pedido.objects.select_related(
            'usuario', 'evento'
        ).prefetch_related('itens', 'itens__lote').get(id=pedido_id)

        if pedido.status != Pedido.StatusPedido.PAGO:
            return {
                'status': 'erro',
                'mensagem': 'Pedido não está pago',
                'pedido_id': pedido_id
            }

        ingressos_criados = []

        for item in pedido.itens.all():
            for _ in range(item.quantidade):
                ingresso = Ingresso.objects.create(
                    usuario=pedido.usuario,
                    evento=pedido.evento,
                    tipo=item.lote.tipo
                )

                qr_buffer = io.BytesIO()
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=4
                )
                qr.add_data(str(ingresso.uuid))
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)

                filename = f'qr_{ingresso.uuid}.png'
                ingresso.qr_code_image.save(filename, File(qr_buffer), save=True)

                ingresso.save()
                ingressos_criados.append(ingresso.id)

                enviar_email_ingresso.delay(ingresso.id)

        return {
            'status': 'success',
            'pedido_id': pedido_id,
            'ingressos_gerados': len(ingressos_criados),
            'ingressos_ids': ingressos_criados
        }

    except Pedido.DoesNotExist:
        return {
            'status': 'erro',
            'mensagem': 'Pedido não encontrado',
            'pedido_id': pedido_id
        }
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def enviar_email_ingresso(self, ingresso_id):
    from apps.tickets.models import Ingresso

    try:
        ingresso = Ingresso.objects.select_related(
            'usuario', 'evento'
        ).get(id=ingresso_id)

        subject = f'Seu ingresso: {ingresso.evento.nome}'

        context = {
            'ingresso': ingresso,
            'usuario': ingresso.usuario,
            'evento': ingresso.evento,
            'qr_code_url': ingresso.qr_code_image.url if ingresso.qr_code_image else None,
            'base_url': settings.BASE_URL
        }

        html_content = render_to_string('emails/ingresso.html', context)
        text_content = render_to_string('emails/ingresso.txt', context)

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ingresso.usuario.email]
        )
        email.content_subtype = 'html'

        if ingresso.qr_code_image:
            email.attach(
                f'ingresso_{ingresso.uuid}.png',
                ingresso.qr_code_image.read(),
                'image/png'
            )

        email.send(fail_silently=False)

        return {
            'status': 'success',
            'ingresso_id': ingresso_id,
            'email_enviado_para': ingresso.usuario.email
        }

    except Ingresso.DoesNotExist:
        return {
            'status': 'erro',
            'mensagem': 'Ingresso não encontrado',
            'ingresso_id': ingresso_id
        }
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def enviar_email_confirmacao_pagamento(pedido_id):
    from apps.orders.models import Pedido

    try:
        pedido = Pedido.objects.select_related(
            'usuario', 'evento'
        ).prefetch_related('itens', 'itens__lote').get(id=pedido_id)

        subject = f'Confirmação de pagamento - {pedido.evento.nome}'

        context = {
            'pedido': pedido,
            'usuario': pedido.usuario,
            'evento': pedido.evento,
            'base_url': settings.BASE_URL
        }

        html_content = render_to_string('emails/pagamento_confirmado.html', context)

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[pedido.usuario.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

        return {
            'status': 'success',
            'pedido_id': pedido_id
        }

    except Pedido.DoesNotExist:
        return {
            'status': 'erro',
            'mensagem': 'Pedido não encontrado'
        }
