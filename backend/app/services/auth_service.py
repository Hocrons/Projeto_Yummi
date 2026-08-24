"""Regras de negocio da autenticacao (RF02, RF03, RF10, RF11).

Login por e-mail ou celular. A verificacao segue uma ordem deliberada:
credencial primeiro, situacao da conta depois. Quem erra a senha recebe sempre
a mesma resposta generica e nao descobre se o e-mail existe; so quem ja provou
saber a senha e informado de que a conta esta pendente ou bloqueada.
"""
from sqlalchemy import select

from app.extensions import db
from app.models.usuario import Usuario
from app.services.usuario_service import conferir_senha
from app.utils.errors import ContaIndisponivel, ErroDeAutenticacao, ErroDeValidacao
from app.utils.validators import so_digitos

MENSAGEM_CONTA_PENDENTE = (
    "Sua conta ainda nao foi verificada. Confirme o codigo enviado para o seu "
    "contato para poder entrar."
)
MENSAGEM_CONTA_BLOQUEADA = (
    "Sua conta esta bloqueada. Procure o suporte do Yummi para desbloquear."
)


def _localizar_usuario(dados):
    """Encontra o usuario pelo e-mail ou pelo celular informado."""
    email = (dados.get("email") or "").strip().lower() or None
    celular = so_digitos(dados.get("celular")) or None

    if not email and not celular:
        raise ErroDeValidacao("identificador", "Informe o e-mail ou o celular.")

    coluna, valor = (Usuario.email, email) if email else (Usuario.celular, celular)
    return db.session.scalar(select(Usuario).where(coluna == valor))


def autenticar(dados):
    """Valida as credenciais e devolve o usuario autenticado.

    Levanta ErroDeAutenticacao (401) quando o par credencial/senha nao confere,
    e ContaIndisponivel (403) quando confere mas a conta nao pode entrar.
    """
    if not isinstance(dados, dict):
        raise ErroDeValidacao("corpo", "O corpo da requisicao deve ser um objeto JSON.")

    senha = dados.get("senha")
    if not senha:
        raise ErroDeValidacao("senha", "Campo obrigatorio.")

    usuario = _localizar_usuario(dados)

    # Conta excluida se comporta como inexistente - nao confirma que existiu.
    if usuario is None or usuario.status_conta == "excluido":
        raise ErroDeAutenticacao()

    # senha_hash e nulo em conta criada por Google/Facebook: nao ha senha local
    # para conferir, entao o login tradicional falha como credencial invalida.
    if not conferir_senha(senha, usuario.senha_hash):
        raise ErroDeAutenticacao()

    # Daqui para baixo a senha ja esta provada: pode explicar o que houve.
    if usuario.status_conta == "pendente":
        raise ContaIndisponivel(MENSAGEM_CONTA_PENDENTE, status_conta="pendente")
    if usuario.status_conta == "bloqueado":
        raise ContaIndisponivel(MENSAGEM_CONTA_BLOQUEADA, status_conta="bloqueado")

    return usuario
