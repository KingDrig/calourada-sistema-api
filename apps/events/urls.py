from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventoViewSet, LoteViewSet, EventoExportView

router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='eventos')
router.register(r'lotes', LoteViewSet, basename='lotes')

urlpatterns = [
    path('', include(router.urls)),
    path('eventos/<int:pk>/exportar-lista/', EventoExportView.as_view(), name='evento-exportar'),
]
