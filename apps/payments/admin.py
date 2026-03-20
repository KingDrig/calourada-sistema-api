from django.contrib import admin
from .models import Pagamento


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'status', 'metodo', 'valor', 'payment_id', 'aprovado_em', 'criado_em']
    list_filter = ['status', 'metodo', 'criado_em']
    search_fields = ['pedido__usuario__username', 'pedido__usuario__email', 'payment_id', 'preference_id']
    readonly_fields = ['payment_id', 'preference_id', 'webhook_payload', 'webhook_received_at', 'aprovado_em']
    autocomplete_fields = ['pedido']
    ordering = ['-criado_em']
