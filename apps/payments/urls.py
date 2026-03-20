from django.urls import path
from .views import (
    MercadoPagoPaymentView,
    MercadoPagoWebhookView,
    PagamentoDetailView
)

urlpatterns = [
    path('payments/criar/', MercadoPagoPaymentView.as_view(), name='payment-create'),
    path('payments/webhook/', MercadoPagoWebhookView.as_view(), name='payment-webhook'),
    path('payments/<int:pk>/', PagamentoDetailView.as_view(), name='payment-detail'),
]
