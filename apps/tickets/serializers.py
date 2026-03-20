from rest_framework import serializers
from .models import Ingresso


class IngressoSerializer(serializers.ModelSerializer):
    evento_nome = serializers.CharField(source='evento.nome', read_only=True)
    evento_data = serializers.DateTimeField(source='evento.data_evento', read_only=True)
    evento_local = serializers.CharField(source='evento.local', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Ingresso
        fields = [
            'id', 'uuid', 'usuario', 'usuario_nome', 'evento',
            'evento_nome', 'evento_data', 'evento_local',
            'tipo', 'tipo_display', 'status', 'status_display',
            'qr_code_image', 'qr_code_url', 'utilizado_em',
            'validado_por', 'criado_em'
        ]
        read_only_fields = [
            'id', 'uuid', 'usuario', 'evento', 'tipo',
            'qr_code_image', 'utilizado_em', 'validado_por', 'criado_em'
        ]

    def get_qr_code_url(self, obj):
        if obj.qr_code_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code_image.url)
            return obj.qr_code_image.url
        return None


class ScannerValidacaoSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
