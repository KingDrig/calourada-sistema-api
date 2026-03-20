from django.contrib import admin
from .models import Evento, Lote


class LoteInline(admin.TabularInline):
    model = Lote
    extra = 1
    fields = ['nome', 'tipo', 'preco', 'quantidade_total', 'quantidade_disponivel', 'data_inicio', 'data_fim', 'ativo']


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'data_evento', 'local', 'capacidade_total', 'ativo', 'criado_em']
    list_filter = ['ativo', 'data_evento']
    search_fields = ['nome', 'descricao', 'local']
    inlines = [LoteInline]
    ordering = ['-data_evento']


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ['evento', 'nome', 'tipo', 'preco', 'quantidade_disponivel', 'quantidade_total', 'esta_disponivel', 'ativo']
    list_filter = ['tipo', 'ativo', 'evento']
    search_fields = ['nome', 'evento__nome']
    autocomplete_fields = ['evento']
    ordering = ['evento', 'data_inicio']
