# Sistema de Venda de Ingressos Universitária

API RESTful para sistema de venda de ingressos de eventos do centro acadêmico.

## Stack Tecnológica

- **Backend**: Django 5.0 + Django REST Framework
- **Banco de Dados**: PostgreSQL
- **Autenticação**: JWT (djangorestframework-simplejwt)
- **Task Queue**: Celery + Redis
- **Pagamentos**: Mercado Pago API
- **QR Code**: qrcode + Pillow
- **Validação**: validate-docbr (CPF)

## Funcionalidades

- [x] Cadastro de usuários com validação de CPF
- [x] Autenticação JWT
- [x] CRUD de Eventos e Lotes
- [x] Checkout com validação de documento (Atestado de Matrícula)
- [x] Aprovação de documentos por Admin
- [x] Integração com Mercado Pago (Pix/Cartão)
- [x] Webhook para notificações de pagamento
- [x] Geração de QR Code com UUID
- [x] Envio de e-mail assíncrono com Celery
- [x] Scanner para validação na porta do evento

## Configuração

### 1. Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:
- `SECRET_KEY`: Chave secreta do Django
- `DATABASE_URL`: URL do banco PostgreSQL
- `MERCADOPAGO_ACCESS_TOKEN`: Token do Mercado Pago
- `MERCADOPAGO_PUBLIC_KEY`: Chave pública do Mercado Pago

### 2. Docker (Recomendado)

```bash
docker-compose up -d
```

Isso iniciará:
- PostgreSQL (porta 5432)
- Redis (porta 6379)
- Django (porta 8000)
- Celery Worker
- Celery Beat
- Flower (monitoramento - porta 5555)

### 3. Instalação Manual

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar banco PostgreSQL
createdb financeiro_db

# Executar migrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver

# Em outro terminal, iniciar Celery
celery -A config worker -l INFO
celery -A config beat -l INFO
```

## Endpoints da API

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/register/` | Cadastro de usuário |
| POST | `/api/auth/login/` | Login JWT |
| POST | `/api/auth/refresh/` | Refresh token |
| GET | `/api/auth/me/` | Dados do usuário |

### Eventos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/eventos/` | Listar eventos |
| GET | `/api/eventos/{id}/` | Detalhes do evento |
| GET | `/api/eventos/{id}/lotes/` | Lotes do evento |
| GET | `/api/lotes/por_evento/?evento_id=X` | Lotes disponíveis |

### Pedidos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/pedidos/` | Criar pedido (checkout) |
| GET | `/api/pedidos/` | Listar pedidos do usuário |
| POST | `/api/documentos/upload/` | Upload de atestado |
| GET | `/api/admin/verificacao/pendentes/` | Docs pendentes (Admin) |
| PATCH | `/api/admin/verificacao/{id}/` | Aprovar/rejeitar (Admin) |

### Pagamentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/payments/criar/` | Criar pagamento MP |
| POST | `/api/payments/webhook/` | Webhook MP |
| GET | `/api/payments/{id}/` | Detalhes do pagamento |

### Ingressos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/ingressos/` | Listar ingressos |
| GET | `/api/ingressos/{uuid}/qr/` | Download QR Code |
| GET | `/api/ingressos/{uuid}/verificar/` | Verificar QR Code |

### Scanner (Staff)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/scanner/validar/` | Validar ingresso |

## Fluxo de Compra

1. Usuário adiciona ingresso ao carrinho
2. Se "Calouro" ou "Veterano", upload do atestado
3. Pedido criado com status `PENDENTE_VALIDACAO`
4. Admin aprova/rejeita o documento
5. Se aprovado, status muda para `APROVADO`
6. Usuário inicia pagamento
7. Webhook confirma pagamento
8. Sistema gera ingresso com QR Code
9. E-mail enviado com Celery

## Permissões

- **Comprador**: Cadastro, login, compra, visualização de próprios dados
- **Staff**: Scanner de validação
- **Admin**: Aprovação de documentos, CRUD completo

## Testes

```bash
# Executar testes
python manage.py test

# Verificar código
python manage.py check
```

## Monitoramento

- **Flower**: http://localhost:5555 (monitoramento Celery)

## Estrutura do Projeto

```
financeiro/
├── apps/
│   ├── accounts/     # Usuários e autenticação
│   ├── events/       # Eventos e lotes
│   ├── orders/       # Pedidos e documentos
│   ├── payments/      # Pagamentos e webhook
│   ├── tickets/       # Ingressos e scanner
│   └── core/          # Configurações base
├── config/            # Configurações Django
├── templates/         # Templates de e-mail
├── docker-compose.yml # Orquestração Docker
└── requirements.txt   # Dependências
```
