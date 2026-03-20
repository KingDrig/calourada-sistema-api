#!/usr/bin/env python3
"""
Script de Teste Completo - Sistema de Ingressos
================================================

Este script simula o fluxo completo de um usuário no sistema:
1. Cadastro de usuário
2. Login e obtenção de token JWT
3. Criação de evento e lote (como Admin)
4. Checkout de ingresso
5. Verificação de pedido

Execute com: python testar_fluxo_completo.py
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta

# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_URL = "http://localhost:8000/api"

class Cores:
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log(tipo, mensagem):
    """Log colorido no terminal"""
    simbolos = {
        'sucesso': f"{Cores.VERDE}✅{Cores.RESET}",
        'info': f"{Cores.AZUL}ℹ️{Cores.RESET}",
        'aviso': f"{Cores.AMARELO}⚠️{Cores.RESET}",
        'erro': f"{Cores.VERMELHO}❌{Cores.RESET}",
        'titulo': f"{Cores.BOLD}{Cores.AZUL}"
    }
    print(f"{simbolos.get(tipo, '')} {mensagem}")

def log_secao(titulo):
    """Imprime uma seção de teste"""
    print(f"\n{'='*60}")
    print(f"{Cores.BOLD}{Cores.AZUL}  {titulo}{Cores.RESET}")
    print(f"{'='*60}\n")

# ============================================================
# DADOS DE TESTE
# ============================================================

# CPF válido para teste (gerado automaticamente)
CPF_TESTE = "529.982.247-25"  # CPF válido do IBGE para testes

USUARIO_COMUM = {
    "username": f"usuario_teste_{int(time.time())}",
    "email": f"usuario_teste_{int(time.time())}@teste.com",
    "password": "teste123456",
    "password_confirm": "teste123456",
    "first_name": "João",
    "last_name": "Silva",
    "telefone": "(11) 99999-9999",
    "cpf": CPF_TESTE,
    "curso": "Ciência da Computação",
    "matricula": f"MAT{int(time.time())}"
}

ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

# ============================================================
# FLUXO DE TESTES
# ============================================================

def testar_cadastro_usuario():
    """Testa o cadastro de um novo usuário"""
    log_secao("1. CADASTRO DE USUÁRIO")
    
    url = f"{BASE_URL}/auth/register/"
    
    log('info', f"Enviando dados para: {url}")
    log('info', f"Username: {USUARIO_COMUM['username']}")
    log('info', f"Email: {USUARIO_COMUM['email']}")
    log('info', f"CPF: {USUARIO_COMUM['cpf']}")
    
    try:
        response = requests.post(url, json=USUARIO_COMUM)
        
        if response.status_code == 201:
            data = response.json()
            log('sucesso', "Usuário cadastrado com sucesso!")
            print(f"\n   Dados do usuário criado:")
            print(f"   - ID: {data['user']['id']}")
            print(f"   - Username: {data['user']['username']}")
            print(f"   - Email: {data['user']['email']}")
            
            # Salvar tokens
            USUARIO_COMUM['access_token'] = data['tokens']['access']
            USUARIO_COMUM['refresh_token'] = data['tokens']['refresh']
            USUARIO_COMUM['user_id'] = data['user']['id']
            
            return True
        else:
            log('erro', f"Falha no cadastro: {response.status_code}")
            log('erro', f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        log('erro', "Não foi possível conectar ao servidor!")
        log('erro', "Certifique-se de que o Django está rodando em http://localhost:8000")
        return False


def testar_login_usuario():
    """Testa o login do usuário comum"""
    log_secao("2. LOGIN DO USUÁRIO COMUM")
    
    url = f"{BASE_URL}/auth/login/"
    
    dados_login = {
        "username": USUARIO_COMUM['username'],
        "password": USUARIO_COMUM['password']
    }
    
    log('info', f"Username: {dados_login['username']}")
    
    try:
        response = requests.post(url, json=dados_login)
        
        if response.status_code == 200:
            data = response.json()
            log('sucesso', "Login realizado com sucesso!")
            print(f"\n   Access Token: {data['access'][:50]}...")
            print(f"   Refresh Token: {data['refresh'][:50]}...")
            
            USUARIO_COMUM['access_token'] = data['access']
            USUARIO_COMUM['refresh_token'] = data['refresh']
            
            return True
        else:
            log('erro', f"Falha no login: {response.status_code}")
            log('erro', f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return False


def testar_login_admin():
    """Testa o login como Admin e retorna o token"""
    log_secao("3. LOGIN COMO ADMIN")
    
    url = f"{BASE_URL}/auth/login/"
    
    log('info', f"Username: {ADMIN_CREDENTIALS['username']}")
    
    try:
        response = requests.post(url, json=ADMIN_CREDENTIALS)
        
        if response.status_code == 200:
            data = response.json()
            log('sucesso', "Login admin realizado com sucesso!")
            admin_token = data['access']
            print(f"\n   Access Token: {admin_token[:50]}...")
            return admin_token
        else:
            log('erro', f"Falha no login admin: {response.status_code}")
            log('erro', f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return None


def testar_criar_evento(admin_token):
    """Testa a criação de um evento (requer Admin)"""
    log_secao("4. CRIAR EVENTO (COMO ADMIN)")
    
    url = f"{BASE_URL}/eventos/"
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    # Evento para daqui a 7 dias
    data_evento = datetime.now() + timedelta(days=7)
    data_evento_str = data_evento.strftime("%Y-%m-%dT%H:%M:%S")
    
    evento_data = {
        "nome": f"Festa do Calouro {datetime.now().year}",
        "descricao": "A melhor festa para receber os calouros!",
        "data_evento": data_evento_str,
        "local": "Centro Acadêmico - Auditório Principal",
        "capacidade_total": 500,
        "ativo": True
    }
    
    log('info', f"Evento: {evento_data['nome']}")
    log('info', f"Data: {data_evento_str}")
    log('info', f"Local: {evento_data['local']}")
    
    try:
        response = requests.post(url, json=evento_data, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            evento_id = data['id']
            log('sucesso', f"Evento criado com sucesso! ID: {evento_id}")
            return evento_id
        else:
            log('erro', f"Falha ao criar evento: {response.status_code}")
            log('erro', f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return None


def testar_criar_lote(admin_token, evento_id):
    """Testa a criação de um lote de ingressos"""
    log_secao("5. CRIAR LOTE DE INGRESSOS (COMO ADMIN)")
    
    url = f"{BASE_URL}/lotes/"
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    data_inicio = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data_fim = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    
    lote_data = {
        "evento": evento_id,
        "nome": "Lote Promocional",
        "tipo": "CALOURO",
        "preco": "25.00",
        "quantidade_total": 100,
        "quantidade_disponivel": 100,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "ativo": True
    }
    
    log('info', f"Lote: {lote_data['nome']}")
    log('info', f"Tipo: {lote_data['tipo']}")
    log('info', f"Preço: R$ {lote_data['preco']}")
    
    try:
        response = requests.post(url, json=lote_data, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            lote_id = data['id']
            log('sucesso', f"Lote criado com sucesso! ID: {lote_id}")
            return lote_id
        else:
            log('erro', f"Falha ao criar lote: {response.status_code}")
            log('erro', f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return None


def testar_checkout():
    """Testa o checkout de um ingresso"""
    log_secao("6. CHECKOUT - ADICIONAR INGRESSO AO CARRINHO")
    
    url = f"{BASE_URL}/pedidos/"
    
    headers = {
        "Authorization": f"Bearer {USUARIO_COMUM['access_token']}",
        "Content-Type": "application/json"
    }
    
    checkout_data = {
        "evento_id": TEST_STATE['evento_id'],
        "itens": [
            {
                "lote_id": TEST_STATE['lote_id'],
                "quantidade": 1
            }
        ]
    }
    
    log('info', f"Evento ID: {checkout_data['evento_id']}")
    log('info', f"Lote ID: {checkout_data['itens'][0]['lote_id']}")
    log('info', f"Quantidade: {checkout_data['itens'][0]['quantidade']}")
    
    try:
        response = requests.post(url, json=checkout_data, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            pedido_id = data['id']
            status = data['status']
            valor = data['valor_total']
            
            log('sucesso', f"Pedido criado! ID: {pedido_id}")
            print(f"\n   Status: {status}")
            print(f"   Valor Total: R$ {valor}")
            
            # Verificar se requer documento
            if data.get('requer_documento'):
                log('aviso', "Pedido requer upload de atestado de matrícula!")
                TEST_STATE['pedido_id'] = pedido_id
                TEST_STATE['status_pedido'] = status
                return pedido_id
            else:
                log('sucesso', "Pedido já aprovado (não requer documento)")
                TEST_STATE['pedido_id'] = pedido_id
                TEST_STATE['status_pedido'] = status
                return pedido_id
        else:
            log('erro', f"Falha no checkout: {response.status_code}")
            log('erro', f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return None


def testar_listar_eventos():
    """Testa listagem de eventos disponíveis"""
    log_secao("7. LISTAR EVENTOS DISPONÍVEIS")
    
    url = f"{BASE_URL}/eventos/"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', len(data.get('results', data)))
            
            log('sucesso', f"Encontrados {count} evento(s)")
            
            if 'results' in data:
                for evento in data['results'][:3]:
                    print(f"\n   - {evento['nome']}")
                    print(f"     Data: {evento['data_evento']}")
                    print(f"     Local: {evento['local']}")
            
            return True
        else:
            log('erro', f"Falha ao listar: {response.status_code}")
            return False
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return False


def testar_meus_dados():
    """Testa endpoint /auth/me/"""
    log_secao("8. VERIFICAR DADOS DO USUÁRIO")
    
    url = f"{BASE_URL}/auth/me/"
    
    headers = {
        "Authorization": f"Bearer {USUARIO_COMUM['access_token']}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log('sucesso', "Dados do usuário retrieved com sucesso!")
            print(f"\n   Nome: {data.get('first_name')} {data.get('last_name')}")
            print(f"   Email: {data.get('email')}")
            print(f"   Curso: {data.get('curso')}")
            print(f"   Matrícula: {data.get('matricula')}")
            return True
        else:
            log('erro', f"Falha: {response.status_code}")
            return False
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return False


def testar_listar_produtos():
    """Testa listagem de produtos da lojinha"""
    log_secao("9. LISTAR PRODUTOS DA LOJINHA")
    
    url = f"{BASE_URL}/produtos/"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            count = len(data)
            
            log('sucesso', f"Encontrados {count} produto(s)")
            
            for produto in data[:3]:
                print(f"\n   - {produto['nome']}")
                print(f"     Preço: R$ {produto['preco']}")
                print(f"     Em estoque: {'Sim' if produto.get('em_estoque') else 'Não'}")
            
            return True
        else:
            log('aviso', f"Nenhum produto encontrado: {response.status_code}")
            return True  # Não é erro crítico
            
    except Exception as e:
        log('erro', f"Erro: {str(e)}")
        return False


# Estado global para compartilhar dados entre testes
TEST_STATE = {}


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():
    """Executa todos os testes em sequência"""
    
    print(f"\n{Cores.BOLD}{'#'*60}")
    print(f"#                                                      #")
    print(f"#     SISTEMA DE INGRESSOS - TESTE DE FLUXO COMPLETO    #")
    print(f"#                                                      #")
    print(f"{'#'*60}{Cores.RESET}\n")
    
    print(f"{Cores.AZUL}Base URL: {BASE_URL}{Cores.RESET}")
    print(f"{Cores.AZUL}CPF de teste: {CPF_TESTE}{Cores.RESET}\n")
    
    # Executar testes em sequência
    testes = [
        ("Cadastro de Usuário", testar_cadastro_usuario),
        ("Login do Usuário", testar_login_usuario),
        ("Login Admin", testar_login_admin),
    ]
    
    admin_token = None
    for nome, teste in testes:
        resultado = teste()
        if nome == "Login Admin" and resultado:
            admin_token = resultado
        if not resultado and nome in ["Cadastro de Usuário", "Login do Usuário"]:
            log('erro', "Fluxo interrompido - falha crítica")
            sys.exit(1)
    
    if not admin_token:
        log('erro', "Não foi possível fazer login como admin")
        log('info', "Verifique se existe um usuário admin criado:")
        log('info', "python manage.py shell -c \"from apps.accounts.models import Usuario;")
        log('info', "Usuario.objects.create_superuser(...)\"")
        sys.exit(1)
    
    # Testes que dependem do admin
    TEST_STATE['admin_token'] = admin_token
    
    evento_id = testar_criar_evento(admin_token)
    if evento_id:
        TEST_STATE['evento_id'] = evento_id
        
        lote_id = testar_criar_lote(admin_token, evento_id)
        if lote_id:
            TEST_STATE['lote_id'] = lote_id
    
    if not evento_id or not lote_id:
        log('aviso', "Não foi possível criar evento/lote")
        log('info', "Pulando teste de checkout")
    else:
        testar_checkout()
    
    # Testes que não dependem de criação
    testar_listar_eventos()
    testar_listar_produtos()
    testar_meus_dados()
    
    # Resumo final
    log_secao("RESUMO DO TESTE")
    
    print(f"""
    {Cores.VERDE}✅ Fluxo de teste concluído!{Cores.RESET}
    
    Dados do usuário criado:
    - Username: {USUARIO_COMUM['username']}
    - Password: {USUARIO_COMUM['password']}
    - Access Token: {USUARIO_COMUM.get('access_token', 'N/A')[:50]}...
    
    Para testar no Swagger:
    1. Abra: http://localhost:8000/api/docs/
    2. Use o token acima no botão "Authorize"
    
    Para rodar o servidor:
    1. docker-compose up -d
    2. ou: python manage.py runserver
    """)


if __name__ == "__main__":
    main()
