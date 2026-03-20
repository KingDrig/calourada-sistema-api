from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngressoViewSet, StaffScannerView, download_qr_code, verificar_qr_code

router = DefaultRouter()
router.register(r'ingressos', IngressoViewSet, basename='ingressos')

urlpatterns = [
    path('', include(router.urls)),
    path('scanner/validar/', StaffScannerView.as_view(), name='scanner-validate'),
    path('ingressos/<uuid:uuid>/qr/', download_qr_code, name='qr-download'),
    path('ingressos/<uuid:uuid>/verificar/', verificar_qr_code, name='qr-verificar'),
]
