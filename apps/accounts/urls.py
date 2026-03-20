from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    MeView,
    TrocarSenhaView,
    LogoutView,
    EsqueciSenhaView,
    RedefinirSenhaView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/trocar-senha/', TrocarSenhaView.as_view(), name='trocar_senha'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/esqueci-senha/', EsqueciSenhaView.as_view(), name='esqueci_senha'),
    path('auth/redifinir-senha/', RedefinirSenhaView.as_view(), name='redefinir_senha'),
]
