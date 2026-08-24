"""Testes do login (RF02, RF03, RF05, RF10, RF11)."""
from tests.conftest import CPF_VALIDO_2

ROTA_LOGIN = "/api/auth/login"
ROTA_USUARIOS = "/api/usuarios"


def _cadastrar_e_ativar(client, usuario_valido):
    """Cria a conta e a ativa, simulando a validacao do codigo OTP."""
    criado = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]
    client.patch(f"{ROTA_USUARIOS}/{criado['id_usuario']}/status", json={"status_conta": "ativo"})
    return criado


def test_login_com_email_e_senha_corretos(client, usuario_valido):
    criado = _cadastrar_e_ativar(client, usuario_valido)

    resposta = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": usuario_valido["senha"]}
    )

    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["id_usuario"] == criado["id_usuario"]


def test_login_com_celular(client, usuario_valido):
    """RF03: o celular tambem serve de identificador."""
    _cadastrar_e_ativar(client, usuario_valido)

    resposta = client.post(
        ROTA_LOGIN, json={"celular": "(11) 98765-4321", "senha": usuario_valido["senha"]}
    )
    assert resposta.status_code == 200


def test_login_aceita_email_com_caixa_diferente(client, usuario_valido):
    _cadastrar_e_ativar(client, usuario_valido)

    resposta = client.post(
        ROTA_LOGIN, json={"email": "  MARIA@Exemplo.COM ", "senha": usuario_valido["senha"]}
    )
    assert resposta.status_code == 200


def test_resposta_do_login_nunca_traz_a_senha(client, usuario_valido):
    _cadastrar_e_ativar(client, usuario_valido)

    corpo = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": usuario_valido["senha"]}
    ).get_json()["dados"]

    assert "senha" not in corpo
    assert "senha_hash" not in corpo


def test_senha_errada_devolve_401(client, usuario_valido):
    _cadastrar_e_ativar(client, usuario_valido)

    resposta = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": "senhaErrada123"}
    )
    assert resposta.status_code == 401


def test_usuario_inexistente_devolve_401(client):
    resposta = client.post(ROTA_LOGIN, json={"email": "ninguem@exemplo.com", "senha": "qualquer1"})
    assert resposta.status_code == 401


def test_usuario_inexistente_e_senha_errada_dao_a_mesma_resposta(client, usuario_valido):
    """Mensagens diferentes revelariam quais e-mails existem na base."""
    _cadastrar_e_ativar(client, usuario_valido)

    senha_errada = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": "senhaErrada123"}
    )
    inexistente = client.post(
        ROTA_LOGIN, json={"email": "ninguem@exemplo.com", "senha": "senhaErrada123"}
    )

    assert senha_errada.status_code == inexistente.status_code == 401
    assert senha_errada.get_json() == inexistente.get_json()


def test_conta_pendente_devolve_403(client, usuario_valido):
    """RF11: conta com OTP pendente nao realiza login completo."""
    client.post(ROTA_USUARIOS, json=usuario_valido)  # nasce pendente, sem ativar

    resposta = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": usuario_valido["senha"]}
    )

    assert resposta.status_code == 403
    assert resposta.get_json()["erro"]["status_conta"] == "pendente"


def test_conta_bloqueada_devolve_403(client, usuario_valido):
    criado = _cadastrar_e_ativar(client, usuario_valido)
    client.patch(f"{ROTA_USUARIOS}/{criado['id_usuario']}/status", json={"status_conta": "bloqueado"})

    resposta = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": usuario_valido["senha"]}
    )

    assert resposta.status_code == 403
    assert resposta.get_json()["erro"]["status_conta"] == "bloqueado"


def test_conta_excluida_devolve_401_e_nao_403(client, usuario_valido):
    """Conta excluida se comporta como inexistente - nao confirma que existiu."""
    criado = _cadastrar_e_ativar(client, usuario_valido)
    client.delete(f"{ROTA_USUARIOS}/{criado['id_usuario']}")

    resposta = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": usuario_valido["senha"]}
    )
    assert resposta.status_code == 401


def test_conta_social_nao_entra_por_senha(client, usuario_valido):
    """RF05: quem se cadastrou pelo Google nao tem senha local."""
    usuario_valido.pop("senha")
    usuario_valido["provedor_social"] = "google"
    usuario_valido["id_social"] = "108423"
    _cadastrar_e_ativar(client, usuario_valido)

    resposta = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": "qualquerSenha1"}
    )
    assert resposta.status_code == 401


def test_login_sem_senha_devolve_400(client, usuario_valido):
    _cadastrar_e_ativar(client, usuario_valido)

    resposta = client.post(ROTA_LOGIN, json={"email": usuario_valido["email"]})
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "senha"


def test_login_sem_identificador_devolve_400(client):
    resposta = client.post(ROTA_LOGIN, json={"senha": "senhaSegura123"})
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "identificador"


def test_nao_entra_com_a_senha_de_outro_usuario(client, usuario_valido):
    _cadastrar_e_ativar(client, usuario_valido)
    outro = dict(usuario_valido, cpf=CPF_VALIDO_2, email="joao@exemplo.com",
                 celular="11912345678", senha="outraSenhaBoa9")
    _cadastrar_e_ativar(client, outro)

    resposta = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": "outraSenhaBoa9"}
    )
    assert resposta.status_code == 401
