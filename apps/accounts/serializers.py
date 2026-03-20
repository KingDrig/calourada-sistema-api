from rest_framework import serializers
from validate_docbr import CPF
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telefone', 'cpf', 'curso', 'matricula',
            'is_admin', 'is_staff_member', 'date_joined'
        ]
        read_only_fields = ['id', 'is_admin', 'is_staff_member', 'date_joined']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'telefone', 'cpf',
            'curso', 'matricula'
        ]

    def validate_cpf(self, value):
        cpf_limpo = value.replace('.', '').replace('-', '')
        cpf_validator = CPF()
        if not cpf_validator.validate(cpf_limpo):
            raise serializers.ValidationError("CPF inválido. Verifique o número digitado.")
        
        if Usuario.objects.filter(cpf=value).exists():
            raise serializers.ValidationError("Este CPF já está cadastrado.")
        
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class TrocarSenhaSerializer(serializers.Serializer):
    senha_atual = serializers.CharField(write_only=True, style={'input_type': 'password'})
    nova_senha = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    nova_senha_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_nova_senha(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("A senha deve ter pelo menos 8 caracteres.")
        return value

    def validate(self, attrs):
        if attrs.get('nova_senha') != attrs.get('nova_senha_confirm'):
            raise serializers.ValidationError({
                'nova_senha_confirm': 'As novas senhas não coincidem.'
            })
        return attrs


class EsqueciSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RedefinirSenhaSerializer(serializers.Serializer):
    token = serializers.CharField()
    nova_senha = serializers.CharField(min_length=8, write_only=True)

    def validate_nova_senha(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("A senha deve ter pelo menos 8 caracteres.")
        return value
