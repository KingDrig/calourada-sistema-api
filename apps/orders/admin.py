from django.contrib import admin
from .models import Pedido, ItemPedido, Documento


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ['lote', 'quantidade', 'preco_unitario']
    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'evento', 'status', 'valor_total', 'total_ingressos', 'criado_em']
    list_filter = ['status', 'evento', 'criado_em']
    search_fields = ['usuario__username', 'usuario__email', 'usuario__cpf', 'evento__nome']
    readonly_fields = ['valor_total', 'criado_em', 'atualizado_em']
    inlines = [ItemPedidoInline]
    autocomplete_fields = ['usuario', 'evento']
    ordering = ['-criado_em']


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'tipo', 'status', 'verificado', 'verificado_por', 'verificado_em']
    list_filter = ['status', 'tipo', 'verificado', 'criado_em']
    search_fields = ['pedido__usuario__username', 'pedido__usuario__cpf']
    readonly_fields = ['status', 'verificado', 'verificado_por', 'verificado_em']
    autocomplete_fields = ['pedido', 'verificado_por']
    ordering = ['-criado_em']
