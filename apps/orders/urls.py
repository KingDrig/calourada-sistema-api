from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PedidoViewSet, DocumentoUploadView, AdminVerificacaoViewSet,
    ItemVendaViewSet, CarrinhoViewSet
)

router = DefaultRouter()
router.register(r'pedidos', PedidoViewSet, basename='pedidos')
router.register(r'admin/verificacao', AdminVerificacaoViewSet, basename='verificacao')
router.register(r'produtos', ItemVendaViewSet, basename='produtos')
router.register(r'carrinho', CarrinhoViewSet, basename='carrinho')

urlpatterns = [
    path('', include(router.urls)),
    path('documentos/upload/', DocumentoUploadView.as_view(), name='documento-upload'),
]
