import io
import qrcode
import qrcode.constants
from django.conf import settings
from django.core.files import File
from rest_framework import permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Ingresso
from .serializers import IngressoSerializer, ScannerValidacaoSerializer
from apps.core.permissions import IsStaffMember


def gerar_qr_code(uuid_ticket: str) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(str(uuid_ticket))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


class IngressoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngressoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Ingresso.objects.select_related(
                'usuario', 'evento', 'validado_por'
            ).all()
        return Ingresso.objects.filter(
            usuario=self.request.user
        ).select_related('evento', 'validado_por')

    @staticmethod
    def gerar_e_salvar_qr_code(ingresso):
        if not ingresso.qr_code_image:
            buffer = gerar_qr_code(str(ingresso.uuid))
            filename = f'qr_{ingresso.uuid}.png'
            ingresso.qr_code_image.save(filename, File(buffer), save=True)
        return ingresso.qr_code_image.url


class StaffScannerView(APIView):
    permission_classes = [IsStaffMember]

    def post(self, request):
        serializer = ScannerValidacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uuid_ticket = serializer.validated_data['uuid']

        try:
            ingresso = Ingresso.objects.select_related(
                'evento', 'usuario'
            ).get(uuid=uuid_ticket)
        except Ingresso.DoesNotExist:
            return Response(
                {
                    'valido': False,
                    'erro': 'INGRESSO NÃO ENCONTRADO',
                    'detalhe': 'Verifique se o código QR está correto.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if ingresso.status == Ingresso.StatusIngresso.CANCELADO:
            return Response(
                {
                    'valido': False,
                    'erro': 'INGRESSO CANCELADO',
                    'ingresso_uuid': str(ingresso.uuid),
                    'detalhe': 'Este ingresso foi cancelado.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if ingresso.status == Ingresso.StatusIngresso.EXPIRADO:
            return Response(
                {
                    'valido': False,
                    'erro': 'INGRESSO EXPIRADO',
                    'ingresso_uuid': str(ingresso.uuid),
                    'detalhe': 'Este ingresso já expirou.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if ingresso.evento.ja_ocorreu:
            return Response(
                {
                    'valido': False,
                    'erro': 'EVENTO JÁ REALIZADO',
                    'ingresso_uuid': str(ingresso.uuid),
                    'evento': ingresso.evento.nome,
                    'data_evento': ingresso.evento.data_evento
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if ingresso.status == Ingresso.StatusIngresso.UTILIZADO:
            return Response(
                {
                    'valido': False,
                    'erro': 'INGRESSO JÁ UTILIZADO',
                    'ingresso_uuid': str(ingresso.uuid),
                    'utilizado_em': ingresso.utilizado_em,
                    'validado_por': ingresso.validado_por.get_full_name() if ingresso.validado_por else None,
                    'detalhe': 'Este ingresso já foi utilizado anteriormente.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ingresso.marcar_utilizado(request.user)
        except ValueError as e:
            return Response(
                {
                    'valido': False,
                    'erro': 'ERRO AO VALIDAR',
                    'detalhe': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'valido': True,
            'mensagem': 'INGRESSO VALIDADO COM SUCESSO',
            'ingresso': IngressoSerializer(ingresso).data
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_qr_code(request, uuid):
    try:
        ingresso = Ingresso.objects.get(uuid=uuid)
    except Ingresso.DoesNotExist:
        return Response(
            {'detail': 'Ingresso não encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if ingresso.usuario != request.user and not request.user.is_admin:
        return Response(
            {'detail': 'Você não tem permissão para acessar este ingresso.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if not ingresso.qr_code_image:
        buffer = gerar_qr_code(str(ingresso.uuid))
        filename = f'qr_{ingresso.uuid}.png'
        ingresso.qr_code_image.save(filename, File(buffer), save=True)

    return Response({
        'uuid': str(ingresso.uuid),
        'qr_code_url': request.build_absolute_uri(ingresso.qr_code_image.url),
        'evento': ingresso.evento.nome,
        'tipo': ingresso.tipo,
        'status': ingresso.status
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verificar_qr_code(request, uuid):
    try:
        ingresso = Ingresso.objects.select_related('evento', 'usuario').get(uuid=uuid)
    except Ingresso.DoesNotExist:
        return Response(
            {'valido': False, 'erro': 'Ingresso não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'valido': ingresso.status == Ingresso.StatusIngresso.VALIDO,
        'status': ingresso.status,
        'status_display': ingresso.get_status_display(),
        'evento': ingresso.evento.nome,
        'tipo': ingresso.tipo,
        'tipo_display': ingresso.get_tipo_display()
    })
