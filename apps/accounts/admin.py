from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'cpf', 'is_admin', 'is_staff_member', 'is_active']
    list_filter = ['is_admin', 'is_staff_member', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'cpf', 'first_name', 'last_name', 'matricula']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Pessoais', {
            'fields': ('telefone', 'cpf', 'curso', 'matricula')
        }),
        ('Permissões Especiais', {
            'fields': ('is_staff_member', 'is_admin')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações Pessoais', {
            'fields': ('telefone', 'cpf', 'curso', 'matricula')
        }),
    )
