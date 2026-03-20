from rest_framework import serializers
from .models import Pagamento


class PagamentoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    metodo_display = serializers.CharField(source='get_metodo_display', read_only=True)
    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True)
    pedido_evento = serializers.CharField(source='pedido.evento.nome', read_only=True)

    class Meta:
        model = Pagamento
        fields = [
            'id', 'pedido', 'pedido_id', 'pedido_evento',
            'status', 'status_display', 'metodo', 'metodo_display',
            'payment_id', 'preference_id', 'external_reference',
            'valor', 'codigo_pix', 'url_pagamento',
            'aprovado_em', 'criado_em'
        ]
        read_only_fields = [
            'id', 'status', 'payment_id', 'preference_id',
            'aprovado_em', 'criado_em'
        ]


class WebhookPayloadSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    action = serializers.CharField()
    api_version = serializers.CharField(required=False)
    data = serializers.DictField(required=False)
    type = serializers.CharField(required=False)
    date_created = serializers.CharField(required=False)
    live_mode = serializers.BooleanField(required=False)
    user_id = serializers.CharField(required=False)


class CriarPagamentoSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField()
    metodo = serializers.ChoiceField(
        choices=['PIX', 'CARTAO_CREDITO', 'CARTAO_DEBITO'],
        required=False
    )
