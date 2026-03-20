from django.db import models
from django.utils import timezone
from apps.core.models import TimestampedModel


class Evento(TimestampedModel):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_evento = models.DateTimeField()
    local = models.CharField(max_length=200)
    imagem = models.ImageField(upload_to='eventos/', blank=True, null=True)
    capacidade_total = models.PositiveIntegerField()
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-data_evento']

    def __str__(self):
        return f"{self.nome} - {self.data_evento.strftime('%d/%m/%Y %H:%M')}"

    @property
    def esta_ocorrendo(self):
        now = timezone.now()
        return self.data_evento <= now

    @property
    def ja_ocorreu(self):
        return timezone.now() > self.data_evento

    @property
    def total_ingressos_vendidos(self):
        from apps.orders.models import Pedido
        return sum(
            sum(item.quantidade for item in pedido.itens.all())
            for pedido in self.pedidos.filter(status__in=['PAGO'])
        )

    @property
    def disponibilidade(self):
        return self.capacidade_total - self.total_ingressos_vendidos


class TipoIngresso(models.TextChoices):
    CALOURO = 'CALOURO', 'Calouro'
    VETERANO = 'VETERANO', 'Veterano'
    EXTERNO = 'EXTERNO', 'Externo'


class Lote(TimestampedModel):
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='lotes'
    )
    nome = models.CharField(max_length=50, help_text="Ex: Lote 1, Promoção, VIP")
    tipo = models.CharField(
        max_length=20,
        choices=TipoIngresso.choices,
        default=TipoIngresso.EXTERNO
    )
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_total = models.PositiveIntegerField()
    quantidade_disponivel = models.PositiveIntegerField()
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['data_inicio']
        unique_together = ['evento', 'nome']

    def __str__(self):
        return f"{self.evento.nome} - {self.nome} ({self.tipo})"

    @property
    def esta_disponivel(self):
        now = timezone.now()
        return (
            self.ativo and
            self.quantidade_disponivel > 0 and
            self.data_inicio <= now <= self.data_fim
        )

    @property
    def requer_documento(self):
        return self.tipo in [TipoIngresso.CALOURO, TipoIngresso.VETERANO]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantidade_disponivel > self.quantidade_total:
            raise ValidationError({
                'quantidade_disponivel': 'Quantidade disponível não pode exceder a quantidade total.'
            })
        if self.data_fim < self.data_inicio:
            raise ValidationError({
                'data_fim': 'Data de fim deve ser posterior à data de início.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
