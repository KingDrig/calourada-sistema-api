from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from validate_docbr import CPF


class Usuario(AbstractUser):
    TELEFONE_HELP = "Formato: (XX) XXXXX-XXXX"
    
    telefone = models.CharField(
        max_length=20,
        blank=True,
        help_text=TELEFONE_HELP
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        help_text="Formato: 000.000.000-00"
    )
    curso = models.CharField(max_length=100, blank=True)
    matricula = models.CharField(max_length=50, unique=True, blank=True)
    is_staff_member = models.BooleanField(
        default=False,
        help_text="Membro staff para scanner de validação"
    )
    is_admin = models.BooleanField(
        default=False,
        help_text="Admin para aprovação de documentos e CRUD"
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def cpf_valido(self) -> bool:
        cpf_validator = CPF()
        cpf_limpo = self.cpf.replace('.', '').replace('-', '')
        return cpf_validator.validate(cpf_limpo)

    def clean(self):
        super().clean()
        if self.cpf:
            if not self.cpf_valido():
                raise ValidationError({'cpf': 'CPF inválido. Verifique o número digitado.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_password_reset_token(self):
        import hashlib
        import time
        token = hashlib.sha256(
            f"{self.id}-{self.email}-{self.password}-{time.time()}".encode()
        ).hexdigest()[:64]
        return token
