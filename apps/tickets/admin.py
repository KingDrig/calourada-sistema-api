from django.contrib import admin
from .models import Ingresso


@admin.register(Ingresso)
class IngressoAdmin(admin.ModelAdmin):
    list_display = ['id', 'uuid', 'usuario', 'evento', 'tipo', 'status', 'utilizado_em', 'criado_em']
    list_filter = ['status', 'tipo', 'evento', 'criado_em']
    search_fields = ['uuid', 'usuario__username', 'usuario__email', 'usuario__cpf', 'evento__nome']
    readonly_fields = ['uuid', 'utilizado_em', 'validado_por', 'criado_em']
    autocomplete_fields = ['usuario', 'evento', 'validado_por']
    ordering = ['-criado_em']
