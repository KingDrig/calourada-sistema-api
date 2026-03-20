from django.db import models
from apps.core.models import TimestampedModel
from apps.orders.models import Pedido


class Pagamento(TimestampedModel):
    class StatusPagamento(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        APROVADO = 'APROVADO', 'Aprovado'
        RECUSADO = 'RECUSADO', 'Recusado'
        ESTORNADO = 'ESTORNADO', 'Estornado'

    class MetodoPagamento(models.TextChoices):
        PIX = 'PIX', 'Pix'
        CARTAO_CREDITO = 'CARTAO_CREDITO', 'Cartão de Crédito'
        CARTAO_DEBITO = 'CARTAO_DEBITO', 'Cartão de Débito'

    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='pagamento'
    )
    status = models.CharField(
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE
    )
    metodo = models.CharField(
        max_length=20,
        choices=MetodoPagamento.choices,
        blank=True
    )
    payment_id = models.CharField(max_length=100, blank=True)
    preference_id = models.CharField(max_length=100, blank=True)
    external_reference = models.CharField(max_length=200, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_pix = models.TextField(blank=True)
    url_pagamento = models.URLField(blank=True)
    aprovado_em = models.DateTimeField(null=True, blank=True)
    webhook_received_at = models.DateTimeField(null=True, blank=True)
    webhook_payload = models.JSONField(default=dict)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Pagamento #{self.id} - {self.pedido} - {self.get_status_display()}"
