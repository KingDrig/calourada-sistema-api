from django.db import models
from django.conf import settings
from apps.core.models import TimestampedModel
from apps.events.models import Evento, Lote


class Pedido(TimestampedModel):
    class StatusPedido(models.TextChoices):
        PENDENTE_VALIDACAO = 'PENDENTE_VALIDACAO', 'Pendente Validação'
        APROVADO = 'APROVADO', 'Aprovado'
        REJEITADO = 'REJEITADO', 'Rejeitado'
        PAGO = 'PAGO', 'Pago'
        CANCELADO = 'CANCELADO', 'Cancelado'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pedidos'
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='pedidos'
    )
    status = models.CharField(
        max_length=30,
        choices=StatusPedido.choices,
        default=StatusPedido.PENDENTE_VALIDACAO
    )
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-criado_em']
        unique_together = ['usuario', 'evento']

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username} - {self.evento.nome}"

    @property
    def total_ingressos(self):
        return sum(item.quantidade for item in self.itens.all())

    @property
    def requer_documento(self):
        return any(
            item.lote.requer_documento
            for item in self.itens.all()
        )

    @property
    def documento_pendente(self):
        if not self.requer_documento:
            return False
        return not hasattr(self, 'documento') or not self.documento.verificado


class ItemPedido(TimestampedModel):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    lote = models.ForeignKey(
        Lote,
        on_delete=models.CASCADE,
        related_name='itens_pedido'
    )
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens dos Pedidos'
        unique_together = ['pedido', 'lote']

    def __str__(self):
        return f"{self.quantidade}x {self.lote.nome} - R$ {self.preco_unitario}"

    def save(self, *args, **kwargs):
        if not self.preco_unitario:
            self.preco_unitario = self.lote.preco
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario


class Documento(TimestampedModel):
    class TipoDocumento(models.TextChoices):
        ATESTADO_MATRICULA = 'ATESTADO_MATRICULA', 'Atestado de Matrícula'

    class StatusDocumento(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        APROVADO = 'APROVADO', 'Aprovado'
        REJEITADO = 'REJEITADO', 'Rejeitado'

    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='documento'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TipoDocumento.choices,
        default=TipoDocumento.ATESTADO_MATRICULA
    )
    arquivo = models.FileField(upload_to='documentos/%Y/%m/%d/')
    status = models.CharField(
        max_length=20,
        choices=StatusDocumento.choices,
        default=StatusDocumento.PENDENTE
    )
    verificado = models.BooleanField(default=False)
    motivo_rejeicao = models.TextField(blank=True)
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_verificados'
    )
    verificado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return f"Documento - {self.pedido} ({self.get_status_display()})"


class ItemVenda(TimestampedModel):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_estoque = models.PositiveIntegerField(default=0)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Item de Venda'
        verbose_name_plural = 'Itens de Venda'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"

    @property
    def em_estoque(self):
        return self.quantidade_estoque > 0 and self.ativo


class ItemCarrinho(TimestampedModel):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrinho'
    )
    item_venda = models.ForeignKey(
        ItemVenda,
        on_delete=models.CASCADE,
        related_name='carrinho'
    )
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'
        unique_together = ['usuario', 'item_venda']

    def __str__(self):
        return f"{self.quantidade}x {self.item_venda.nome}"

    @property
    def subtotal(self):
        return self.quantidade * self.item_venda.preco
