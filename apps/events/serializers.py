from rest_framework import serializers
from .models import Evento, Lote, TipoIngresso


class LoteSerializer(serializers.ModelSerializer):
    esta_disponivel = serializers.BooleanField(read_only=True)
    requer_documento = serializers.BooleanField(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Lote
        fields = [
            'id', 'evento', 'nome', 'tipo', 'tipo_display', 'preco',
            'quantidade_total', 'quantidade_disponivel', 'data_inicio',
            'data_fim', 'ativo', 'esta_disponivel', 'requer_documento'
        ]
        read_only_fields = ['id']


class LoteDetailSerializer(serializers.ModelSerializer):
    esta_disponivel = serializers.BooleanField(read_only=True)
    requer_documento = serializers.BooleanField(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    evento_nome = serializers.CharField(source='evento.nome', read_only=True)

    class Meta:
        model = Lote
        fields = [
            'id', 'evento', 'evento_nome', 'nome', 'tipo', 'tipo_display',
            'preco', 'quantidade_total', 'quantidade_disponivel',
            'data_inicio', 'data_fim', 'ativo', 'esta_disponivel',
            'requer_documento', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id']


class EventoSerializer(serializers.ModelSerializer):
    disponibilidade = serializers.IntegerField(read_only=True)
    total_ingressos_vendidos = serializers.IntegerField(read_only=True)
    ja_ocorreu = serializers.BooleanField(read_only=True)
    lotes_disponiveis = serializers.SerializerMethodField()

    class Meta:
        model = Evento
        fields = [
            'id', 'nome', 'descricao', 'data_evento', 'local', 'imagem',
            'capacidade_total', 'ativo', 'disponibilidade',
            'total_ingressos_vendidos', 'ja_ocorreu', 'lotes_disponiveis',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id']

    def get_lotes_disponiveis(self, obj):
        from django.utils import timezone
        now = timezone.now()
        lotes = obj.lotes.filter(
            ativo=True,
            quantidade_disponivel__gt=0,
            data_inicio__lte=now,
            data_fim__gte=now
        )
        return LoteSerializer(lotes, many=True).data


class EventoDetailSerializer(serializers.ModelSerializer):
    disponibilidade = serializers.IntegerField(read_only=True)
    total_ingressos_vendidos = serializers.IntegerField(read_only=True)
    ja_ocorreu = serializers.BooleanField(read_only=True)
    lotes = LoteSerializer(many=True, read_only=True)

    class Meta:
        model = Evento
        fields = [
            'id', 'nome', 'descricao', 'data_evento', 'local', 'imagem',
            'capacidade_total', 'ativo', 'disponibilidade',
            'total_ingressos_vendidos', 'ja_ocorreu', 'lotes',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id']
