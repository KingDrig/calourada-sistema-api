from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage


@shared_task(bind=True, max_retries=3)
def enviar_email_recuperacao_senha(self, user_id, reset_url):
    from apps.accounts.models import Usuario
    
    try:
        user = Usuario.objects.get(id=user_id)
        
        subject = 'Recuperação de Senha - Centro Acadêmico'
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Olá, {user.get_full_name() or user.username}!</h2>
            <p>Você solicitou a recuperação de senha.</p>
            <p>Clique no botão abaixo para redefinir sua senha:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Redefinir Senha</a>
            </p>
            <p>Ou copie e cole este link no seu navegador:</p>
            <p style="word-break: break-all; color: #3498db;">{reset_url}</p>
            <p style="color: #e74c3c;"><strong>Este link expira em 24 horas.</strong></p>
            <p>Se você não solicitou a recuperação de senha, ignore este e-mail.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Centro Acadêmico</p>
        </body>
        </html>
        """
        
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        
        return {'status': 'success', 'email': user.email}
    
    except Usuario.DoesNotExist:
        return {'status': 'erro', 'mensagem': 'Usuário não encontrado'}
    except Exception as exc:
        raise self.retry(exc=exc)
