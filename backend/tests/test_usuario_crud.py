"""Testes do CRUD de usuario.

Cobrem os requisitos funcionais do modulo de Cadastro de Usuario:
RF01, RF07, RF08, RF09 e RF11.
"""
import pytest

from app.extensions import db
from app.models.usuario import Usuario
from app.services.usuario_service import conferir_senha
from app.utils.validators import validar_cpf
from tests.conftest import CPF_INVALIDO, CPF_VALIDO, CPF_VALIDO_2

ROTA = "/api/usuarios"


# ------------------------------------------------------- RF07: validacao de CPF

@pytest.mark.parametrize("cpf", [CPF_VALIDO, CPF_VALIDO_2, "529.982.247-25"])
def test_cpf_valido_e_aceito(cpf):
    assert validar_cpf(cpf) is True


@pytest.mark.parametrize(
    "cpf",
    [
        CPF_INVALIDO,      # digito verificador errado
        "11111111111",     # todos os digitos iguais
        "00000000000",
        "123456789",       # curto demais
        "529982247250",    # longo demais
        "",
        None,
    ],
)
def test_cpf_invalido_e_recusado(cpf):
    assert validar_cpf(cpf) is False


# ------------------------------------------------------------- CREATE (RF01)

def test_cria_usuario_com_dados_validos(client, usuario_valido):
    resposta = client.post(ROTA, json=usuario_valido)

    assert resposta.status_code == 201
    corpo = resposta.get_json()["dados"]
    assert corpo["nome_completo"] == "Maria de Souza"
    assert corpo["cpf"] == CPF_VALIDO
    # RF11: a conta nasce pendente, ate a validacao do OTP.
    assert corpo["status_conta"] == "pendente"
    assert corpo["tipo_usuario"] == "cliente"


def test_resposta_nunca_expoe_a_senha(client, usuario_valido):
    corpo = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    assert "senha" not in corpo
    assert "senha_hash" not in corpo


def test_senha_e_gravada_como_hash(client, app, usuario_valido):
    """RF09: a senha nunca fica em texto puro no banco."""
    client.post(ROTA, json=usuario_valido)

    usuario = db.session.query(Usuario).filter_by(cpf=CPF_VALIDO).one()
    assert usuario.senha_hash != usuario_valido["senha"]
    assert usuario.senha_hash.startswith("$2b$")
    assert conferir_senha(usuario_valido["senha"], usuario.senha_hash) is True
    assert conferir_senha("senhaErrada", usuario.senha_hash) is False


def test_email_e_normalizado_para_minusculas(client, usuario_valido):
    usuario_valido["email"] = "  MARIA@Exemplo.COM  "
    corpo = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    assert corpo["email"] == "maria@exemplo.com"


def test_celular_e_gravado_so_com_digitos(client, usuario_valido):
    usuario_valido["celular"] = "(11) 98765-4321"
    corpo = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    assert corpo["celular"] == "11987654321"


def test_recusa_cpf_invalido(client, usuario_valido):
    usuario_valido["cpf"] = CPF_INVALIDO
    resposta = client.post(ROTA, json=usuario_valido)

    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "cpf"


def test_recusa_menor_de_18_anos(client, usuario_valido):
    usuario_valido["data_nascimento"] = "2020-01-01"
    resposta = client.post(ROTA, json=usuario_valido)

    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "data_nascimento"


def test_recusa_cadastro_sem_email_e_sem_celular(client, usuario_valido):
    usuario_valido.pop("email")
    usuario_valido.pop("celular")
    resposta = client.post(ROTA, json=usuario_valido)

    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "contato"


def test_recusa_senha_curta(client, usuario_valido):
    usuario_valido["senha"] = "123"
    resposta = client.post(ROTA, json=usuario_valido)

    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "senha"


def test_cadastro_social_dispensa_senha(client, usuario_valido):
    """RF05: quem entra por Google/Facebook nao tem senha local."""
    usuario_valido.pop("senha")
    usuario_valido["provedor_social"] = "google"
    usuario_valido["id_social"] = "108423"

    resposta = client.post(ROTA, json=usuario_valido)
    assert resposta.status_code == 201
    assert resposta.get_json()["dados"]["provedor_social"] == "google"


# -------------------------------------------------------- RF08: unicidade

@pytest.mark.parametrize("campo", ["cpf", "email", "celular"])
def test_recusa_identificador_duplicado(client, usuario_valido, campo):
    client.post(ROTA, json=usuario_valido)

    segundo = dict(usuario_valido)
    # Muda todos os identificadores, menos o que esta sendo testado.
    if campo != "cpf":
        segundo["cpf"] = CPF_VALIDO_2
    if campo != "email":
        segundo["email"] = "outro@exemplo.com"
    if campo != "celular":
        segundo["celular"] = "11912345678"

    resposta = client.post(ROTA, json=segundo)
    assert resposta.status_code == 409
    assert resposta.get_json()["erro"]["campo"] == campo


# ---------------------------------------------------------------- READ

def test_busca_usuario_por_id(client, usuario_valido):
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    resposta = client.get(f"{ROTA}/{criado['id_usuario']}")
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["id_usuario"] == criado["id_usuario"]


def test_busca_id_inexistente_retorna_404(client):
    assert client.get(f"{ROTA}/9999").status_code == 404


def test_lista_usuarios_com_paginacao(client, usuario_valido):
    client.post(ROTA, json=usuario_valido)
    segundo = dict(usuario_valido, cpf=CPF_VALIDO_2, email="joao@exemplo.com",
                   celular="11912345678", nome_completo="Joao Lima")
    client.post(ROTA, json=segundo)

    corpo = client.get(f"{ROTA}?por_pagina=1&pagina=1").get_json()
    assert corpo["paginacao"]["total"] == 2
    assert corpo["paginacao"]["total_paginas"] == 2
    assert len(corpo["dados"]) == 1


def test_lista_filtra_por_tipo_de_usuario(client, usuario_valido):
    client.post(ROTA, json=usuario_valido)
    entregador = dict(usuario_valido, cpf=CPF_VALIDO_2, email="ze@exemplo.com",
                      celular="11912345678", tipo_usuario="entregador")
    client.post(ROTA, json=entregador)

    corpo = client.get(f"{ROTA}?tipo_usuario=entregador").get_json()
    assert corpo["paginacao"]["total"] == 1
    assert corpo["dados"][0]["tipo_usuario"] == "entregador"


# ---------------------------------------------------------------- UPDATE

def test_atualiza_nome(client, usuario_valido):
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    resposta = client.patch(
        f"{ROTA}/{criado['id_usuario']}", json={"nome_completo": "Maria Souza Lima"}
    )
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["nome_completo"] == "Maria Souza Lima"


def test_atualizacao_parcial_preserva_os_demais_campos(client, usuario_valido):
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    atualizado = client.patch(
        f"{ROTA}/{criado['id_usuario']}", json={"nome_completo": "Maria S. Lima"}
    ).get_json()["dados"]

    assert atualizado["email"] == criado["email"]
    assert atualizado["celular"] == criado["celular"]
    assert atualizado["cpf"] == criado["cpf"]


def test_recusa_alteracao_de_cpf(client, usuario_valido):
    """CPF e a chave de negocio da pessoa: nao muda por esta rota."""
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    resposta = client.patch(f"{ROTA}/{criado['id_usuario']}", json={"cpf": CPF_VALIDO_2})
    assert resposta.status_code == 400


def test_recusa_atualizar_para_email_de_outro_usuario(client, usuario_valido):
    primeiro = client.post(ROTA, json=usuario_valido).get_json()["dados"]
    segundo = dict(usuario_valido, cpf=CPF_VALIDO_2, email="joao@exemplo.com",
                   celular="11912345678")
    client.post(ROTA, json=segundo)

    resposta = client.patch(f"{ROTA}/{primeiro['id_usuario']}",
                            json={"email": "joao@exemplo.com"})
    assert resposta.status_code == 409


def test_permite_regravar_o_proprio_email(client, usuario_valido):
    """A checagem de unicidade nao pode acusar conflito com o proprio registro."""
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    resposta = client.patch(f"{ROTA}/{criado['id_usuario']}",
                            json={"email": usuario_valido["email"]})
    assert resposta.status_code == 200


def test_recusa_remover_o_ultimo_contato(client, usuario_valido):
    """Sem e-mail e sem celular o usuario ficaria sem como receber o OTP."""
    usuario_valido.pop("celular")
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    resposta = client.patch(f"{ROTA}/{criado['id_usuario']}", json={"email": ""})
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "contato"


def test_altera_status_para_ativo(client, usuario_valido):
    """RF11: apos validar o OTP, a conta sai de pendente."""
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    resposta = client.patch(f"{ROTA}/{criado['id_usuario']}/status",
                            json={"status_conta": "ativo"})
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["status_conta"] == "ativo"


# ---------------------------------------------------------------- DELETE

def test_exclusao_e_logica_e_preserva_a_linha(client, app, usuario_valido):
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]

    assert client.delete(f"{ROTA}/{criado['id_usuario']}").status_code == 200
    # A rota deixa de encontrar...
    assert client.get(f"{ROTA}/{criado['id_usuario']}").status_code == 404
    # ...mas a linha continua no banco, marcada como excluida.
    usuario = db.session.get(Usuario, criado["id_usuario"])
    assert usuario is not None
    assert usuario.status_conta == "excluido"


def test_usuario_excluido_some_da_listagem(client, usuario_valido):
    criado = client.post(ROTA, json=usuario_valido).get_json()["dados"]
    client.delete(f"{ROTA}/{criado['id_usuario']}")

    assert client.get(ROTA).get_json()["paginacao"]["total"] == 0


def test_exclui_id_inexistente_retorna_404(client):
    assert client.delete(f"{ROTA}/9999").status_code == 404
