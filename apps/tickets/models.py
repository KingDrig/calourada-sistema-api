import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimestampedModel
from apps.events.models import Evento, TipoIngresso


class Ingresso(TimestampedModel):
    class StatusIngresso(models.TextChoices):
        VALIDO = 'VALIDO', 'Válido'
        UTILIZADO = 'UTILIZADO', 'Já Utilizado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        EXPIRADO = 'EXPIRADO', 'Expirado'

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ingressos'
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='ingressos'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoIngresso.choices
    )
    status = models.CharField(
        max_length=20,
        choices=StatusIngresso.choices,
        default=StatusIngresso.VALIDO
    )
    qr_code_image = models.ImageField(
        upload_to='qrcodes/%Y/%m/',
        blank=True,
        null=True
    )
    utilizado_em = models.DateTimeField(null=True, blank=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ingressos_validados'
    )

    class Meta:
        verbose_name = 'Ingresso'
        verbose_name_plural = 'Ingressos'
        ordering = ['-criado_em']
        unique_together = ['usuario', 'evento', 'uuid']

    def __str__(self):
        return f"{self.usuario.username} - {self.evento.nome} ({self.tipo})"

    def marcar_utilizado(self, staff_user):
        from django.utils import timezone
        if self.status == self.StatusIngresso.UTILIZADO:
            raise ValueError("Este ingresso já foi utilizado.")
        if self.status == self.StatusIngresso.CANCELADO:
            raise ValueError("Este ingresso foi cancelado.")
        
        self.status = self.StatusIngresso.UTILIZADO
        self.utilizado_em = timezone.now()
        self.validado_por = staff_user
        self.save()

    def cancelar(self):
        if self.status == self.StatusIngresso.UTILIZADO:
            raise ValueError("Não é possível cancelar um ingresso já utilizado.")
        
        self.status = self.StatusIngresso.CANCELADO
        self.save()
