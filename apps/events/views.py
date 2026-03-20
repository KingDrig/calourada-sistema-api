from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Evento, Lote
from .serializers import (
    EventoSerializer, EventoDetailSerializer,
    LoteSerializer, LoteDetailSerializer
)
from apps.core.permissions import IsAdminUser


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao', 'local']
    ordering_fields = ['data_evento', 'criado_em']
    ordering = ['-data_evento']

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated or not (self.request.user.is_admin or self.request.user.is_staff_member):
            queryset = queryset.filter(ativo=True)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventoDetailSerializer
        return EventoSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdminUser()]

    @action(detail=True, methods=['get'])
    def lotes(self, request, pk=None):
        evento = self.get_object()
        now = timezone.now()
        lotes = evento.lotes.filter(
            ativo=True,
            quantidade_disponivel__gt=0,
            data_inicio__lte=now,
            data_fim__gte=now
        )
        serializer = LoteSerializer(lotes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximos(self, request):
        now = timezone.now()
        eventos = self.get_queryset().filter(
            data_evento__gte=now
        ).order_by('data_evento')[:10]
        serializer = self.get_serializer(eventos, many=True)
        return Response(serializer.data)


class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.select_related('evento').all()
    serializer_class = LoteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['evento', 'tipo', 'ativo']
    search_fields = ['nome', 'evento__nome']
    ordering = ['evento', 'data_inicio']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LoteDetailSerializer
        return LoteSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'])
    def por_evento(self, request):
        evento_id = request.query_params.get('evento_id')
        if not evento_id:
            return Response(
                {'detail': 'Parâmetro evento_id é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()
        lotes = self.queryset.filter(
            evento_id=evento_id,
            ativo=True,
            quantidade_disponivel__gt=0,
            data_inicio__lte=now,
            data_fim__gte=now
        )
        serializer = self.get_serializer(lotes, many=True)
        return Response(serializer.data)


from rest_framework.views import APIView
from django.http import HttpResponse
import csv


class EventoExportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        from apps.tickets.models import Ingresso
        from django.shortcuts import get_object_or_404
        
        evento = get_object_or_404(Evento, pk=pk)
        
        ingressoses = Ingresso.objects.filter(
            evento=evento
        ).select_related('usuario').order_by('usuario__first_name')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="lista_presenca_{evento.id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Nome', 'Matrícula', 'CPF', 'Email', 'Tipo Ingresso', 'Status', 'Utilizado em', 'Validado por'])
        
        for ingresso in ingressoses:
            writer.writerow([
                ingresso.usuario.get_full_name(),
                ingresso.usuario.matricula or '',
                ingresso.usuario.cpf or '',
                ingresso.usuario.email or '',
                ingresso.get_tipo_display(),
                ingresso.get_status_display(),
                ingresso.utilizado_em.strftime('%d/%m/%Y %H:%M:%S') if ingresso.utilizado_em else 'Não utilizado',
                ingresso.validado_por.get_full_name() if ingresso.validado_por else ''
            ])
        
        return response
