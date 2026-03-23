#!/usr/bin/env python
"""Script para criar usuário de teste no banco de dados."""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/home/willian/calourada/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Usuario
from validate_docbr import CPF

# Criar usuário de teste
user = Usuario(
    username='maria.silva',
    email='maria.silva@universidade.br',
    first_name='Maria',
    last_name='Eduarda Silva',
    cpf='12345678900',  # CPF válido sem pontuação
    telefone='91999990000',
    is_admin=False,
    is_staff_member=False,
)
user.set_password('CASIPass2026')
user.save(force_insert=True)

print(f"✅ Usuário criado: {user.email}")
