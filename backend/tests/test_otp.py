"""Testes do codigo de verificacao por e-mail (RF04, RF10, RF11)."""
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models.codigo_otp import MAX_TENTATIVAS, CodigoOtp
from app.models.usuario import Usuario
from app.services import otp_service
from app.utils.errors import ErroDeValidacao

ROTA_USUARIOS = "/api/usuarios"
ROTA_ENVIAR = "/api/verificacao/enviar"
ROTA_VALIDAR = "/api/verificacao/validar"
ROTA_LOGIN = "/api/auth/login"


def _codigo_gravado(id_usuario):
    """Le o codigo direto do banco - o teste nao tem acesso ao e-mail."""
    return db.session.scalars(
        db.select(CodigoOtp)
        .where(CodigoOtp.id_usuario == id_usuario)
        .order_by(CodigoOtp.id_otp.desc())
    ).first()


# ------------------------------------------------------------ geracao

def test_cadastro_dispara_o_envio_do_codigo(client, usuario_valido):
    """O cadastro nao termina sem um codigo gerado para o usuario."""
    resposta = client.post(ROTA_USUARIOS, json=usuario_valido)
    assert resposta.status_code == 201

    id_usuario = resposta.get_json()["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)

    assert registro is not None
    assert registro.finalidade == "cadastro"
    assert registro.canal == "email"
    assert registro.validado is False


def test_codigo_tem_seis_digitos(client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)

    assert len(registro.codigo) == 6
    assert registro.codigo.isdigit()


def test_codigo_expira_em_cinco_minutos(client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)

    duracao = registro.expira_em - registro.criado_em
    assert duracao == timedelta(minutes=5)


def test_resposta_do_cadastro_nao_vaza_o_codigo(client, usuario_valido):
    """O codigo so pode chegar pelo e-mail, nunca pelo corpo da resposta."""
    corpo = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()
    id_usuario = corpo["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)

    assert registro.codigo not in str(corpo)


# ------------------------------------------------------------ validacao

def test_codigo_correto_ativa_a_conta(client, usuario_valido):
    """RF11: e a validacao do codigo que tira a conta de 'pendente'."""
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)

    resposta = client.post(
        ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": registro.codigo}
    )

    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["status_conta"] == "ativo"


def test_login_passa_a_funcionar_depois_da_validacao(client, usuario_valido):
    """O teste que fecha a cadeia: cadastrar, verificar e entrar."""
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]

    # Antes de validar, o login e barrado por conta pendente.
    antes = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": usuario_valido["senha"]}
    )
    assert antes.status_code == 403

    registro = _codigo_gravado(id_usuario)
    client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": registro.codigo})

    depois = client.post(
        ROTA_LOGIN, json={"email": usuario_valido["email"], "senha": usuario_valido["senha"]}
    )
    assert depois.status_code == 200


def test_codigo_errado_devolve_400_e_conta_a_tentativa(client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]

    resposta = client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": "000000"})

    assert resposta.status_code == 400
    assert _codigo_gravado(id_usuario).tentativas == 1


def test_conta_continua_pendente_apos_codigo_errado(client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": "000000"})

    assert db.session.get(Usuario, id_usuario).status_conta == "pendente"


def test_bloqueia_apos_cinco_tentativas(client, usuario_valido):
    """RF10: cinco erros queimam o codigo, mesmo que o certo venha depois."""
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    correto = _codigo_gravado(id_usuario).codigo
    errado = "111111" if correto != "111111" else "222222"

    for _ in range(MAX_TENTATIVAS):
        client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": errado})

    resposta = client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": correto})
    assert resposta.status_code == 400
    assert db.session.get(Usuario, id_usuario).status_conta == "pendente"


def test_codigo_nao_serve_duas_vezes(client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    codigo = _codigo_gravado(id_usuario).codigo

    client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": codigo})
    segunda = client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario, "codigo": codigo})

    assert segunda.status_code == 400


def test_validar_sem_codigo_devolve_400(client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]

    resposta = client.post(ROTA_VALIDAR, json={"id_usuario": id_usuario})
    assert resposta.status_code == 400


def test_validar_usuario_inexistente_devolve_404(client):
    resposta = client.post(ROTA_VALIDAR, json={"id_usuario": 9999, "codigo": "123456"})
    assert resposta.status_code == 404


# --------------------------------------------- expiracao e reenvio (no service)
# Estes usam o parametro `agora` do service: injetar o relogio evita
# `sleep` no teste e deixa a suite rodando em segundos.

def test_codigo_expirado_e_recusado(app, client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)

    seis_minutos_depois = registro.criado_em + timedelta(minutes=6)
    with pytest.raises(ErroDeValidacao, match="expirou"):
        otp_service.validar_codigo(id_usuario, registro.codigo, agora=seis_minutos_depois)


def test_reenvio_antes_de_60s_e_recusado(app, client, usuario_valido):
    """RF04: reenvio so libera depois de 60 segundos."""
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)

    trinta_segundos = registro.criado_em + timedelta(seconds=30)
    with pytest.raises(ErroDeValidacao, match="Aguarde"):
        otp_service.enviar_codigo(id_usuario, agora=trinta_segundos)


def test_reenvio_apos_60s_gera_codigo_novo(app, client, usuario_valido):
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    primeiro = _codigo_gravado(id_usuario)

    depois = primeiro.criado_em + timedelta(seconds=61)
    segundo, _ = otp_service.enviar_codigo(id_usuario, agora=depois)

    assert segundo.id_otp != primeiro.id_otp
    assert segundo.validado is False


def test_reenvio_pela_rota_devolve_expiracao(client, usuario_valido):
    """Sem SMTP configurado nos testes, a API avisa que nao enviou por e-mail."""
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]
    registro = _codigo_gravado(id_usuario)
    registro.criado_em = datetime.now() - timedelta(seconds=90)
    db.session.commit()

    resposta = client.post(ROTA_ENVIAR, json={"id_usuario": id_usuario})

    assert resposta.status_code == 200
    corpo = resposta.get_json()["dados"]
    assert corpo["enviado_por_email"] is False
    assert corpo["expira_em"]


def test_usuario_so_com_celular_nao_recebe_por_email(client, usuario_valido):
    usuario_valido.pop("email")
    id_usuario = client.post(ROTA_USUARIOS, json=usuario_valido).get_json()["dados"]["id_usuario"]

    resposta = client.post(ROTA_ENVIAR, json={"id_usuario": id_usuario})
    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["campo"] == "email"
