from rest_framework import serializers
from .models import Pedido, ItemPedido, Documento, ItemVenda, ItemCarrinho
from apps.events.serializers import LoteSerializer


class DocumentoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    verificado_por_nome = serializers.CharField(
        source='verificado_por.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Documento
        fields = [
            'id', 'pedido', 'tipo', 'tipo_display', 'arquivo',
            'status', 'status_display', 'verificado', 'motivo_rejeicao',
            'verificado_por', 'verificado_por_nome', 'verificado_em',
            'criado_em'
        ]
        read_only_fields = [
            'id', 'status', 'verificado', 'verificado_por',
            'verificado_em', 'criado_em'
        ]


class DocumentoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ['id', 'tipo', 'arquivo']
        read_only_fields = ['id']


class ItemPedidoSerializer(serializers.ModelSerializer):
    lote_nome = serializers.CharField(source='lote.nome', read_only=True)
    tipo_ingresso = serializers.CharField(source='lote.tipo', read_only=True)
    tipo_display = serializers.CharField(source='lote.get_tipo_display', read_only=True)
    requer_documento = serializers.BooleanField(source='lote.requer_documento', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            'id', 'lote', 'lote_nome', 'tipo_ingresso', 'tipo_display',
            'quantidade', 'preco_unitario', 'requer_documento', 'subtotal'
        ]
        read_only_fields = ['id', 'preco_unitario', 'subtotal']


class ItemVendaSerializer(serializers.ModelSerializer):
    em_estoque = serializers.BooleanField(read_only=True)

    class Meta:
        model = ItemVenda
        fields = [
            'id', 'nome', 'descricao', 'preco', 
            'quantidade_estoque', 'em_estoque', 'imagem'
        ]


class ItemCarrinhoSerializer(serializers.ModelSerializer):
    produto = ItemVendaSerializer(source='item_venda', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrinho
        fields = ['id', 'item_venda', 'produto', 'quantidade', 'subtotal']
        read_only_fields = ['id', 'subtotal']


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    evento_nome = serializers.CharField(source='evento.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_ingressos = serializers.IntegerField(read_only=True)
    requer_documento = serializers.BooleanField(read_only=True)
    documento_pendente = serializers.BooleanField(read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'usuario', 'usuario_nome', 'usuario_email', 'evento',
            'evento_nome', 'status', 'status_display', 'valor_total',
            'itens', 'total_ingressos', 'requer_documento',
            'documento_pendente', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = [
            'id', 'usuario', 'status', 'valor_total', 'criado_em', 'atualizado_em'
        ]


class PedidoDetailSerializer(PedidoSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    documento = DocumentoSerializer(read_only=True)

    class Meta(PedidoSerializer.Meta):
        fields = PedidoSerializer.Meta.fields + ['documento']


class CheckoutItemSerializer(serializers.Serializer):
    lote_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1)


class CarrinhoItemSerializer(serializers.Serializer):
    item_venda_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    evento_id = serializers.IntegerField(required=False, allow_null=True)
    itens = CheckoutItemSerializer(many=True, required=False, default=[])
    produtos = CarrinhoItemSerializer(many=True, required=False, default=[])

    def validate(self, attrs):
        if not attrs.get('itens') and not attrs.get('produtos'):
            raise serializers.ValidationError("Informe itens ou produtos.")
        return attrs


class AdminVerificacaoSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APROVADO', 'REJEITADO'])
    motivo_rejeicao = serializers.CharField(required=False, allow_blank=True, max_length=500)
