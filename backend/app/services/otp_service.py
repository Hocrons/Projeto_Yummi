"""Geracao, envio e validacao do codigo de verificacao (RF04, RF10, RF11).

Regras vindas do RF04: codigo numerico de 6 digitos, validade de 5 minutos,
reenvio liberado apos 60 segundos e bloqueio depois de 5 tentativas erradas.
"""
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select

from app.extensions import db
from app.models.codigo_otp import (
    INTERVALO_REENVIO_SEGUNDOS,
    MAX_TENTATIVAS,
    VALIDADE_MINUTOS,
    CodigoOtp,
)
from app.models.usuario import Usuario
from app.utils.email import FalhaNoEnvio, enviar_email, montar_email_de_codigo
from app.utils.errors import ErroDeValidacao, NaoEncontrado


def _gerar_codigo():
    """Seis digitos sorteados com o gerador criptografico, nao com random()."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _ultimo_codigo(id_usuario, finalidade):
    return db.session.scalar(
        select(CodigoOtp)
        .where(CodigoOtp.id_usuario == id_usuario, CodigoOtp.finalidade == finalidade)
        .order_by(CodigoOtp.id_otp.desc())
    )


def _segundos_desde(momento, agora):
    return (agora - momento).total_seconds()


def enviar_codigo(id_usuario, finalidade="cadastro", agora=None):
    """Gera um codigo, grava e tenta enviar por e-mail.

    Devolve (codigo_otp, enviado_por_email). `enviado_por_email` e False quando
    nao ha SMTP configurado - ai o codigo saiu no log do backend.
    """
    agora = agora or datetime.now()

    usuario = db.session.get(Usuario, id_usuario)
    if usuario is None or usuario.status_conta == "excluido":
        raise NaoEncontrado(f"Usuario {id_usuario} nao encontrado.")
    if not usuario.email:
        raise ErroDeValidacao(
            "email", "Este usuario nao tem e-mail cadastrado para receber o codigo."
        )

    # RF04: reenvio so depois de 60 segundos.
    anterior = _ultimo_codigo(id_usuario, finalidade)
    if anterior is not None and not anterior.validado:
        espera = _segundos_desde(anterior.criado_em, agora)
        if espera < INTERVALO_REENVIO_SEGUNDOS:
            faltam = int(INTERVALO_REENVIO_SEGUNDOS - espera)
            raise ErroDeValidacao(
                "codigo", f"Aguarde {faltam} segundos para pedir um novo codigo."
            )

    codigo = CodigoOtp(
        id_usuario=id_usuario,
        codigo=_gerar_codigo(),
        canal="email",
        finalidade=finalidade,
        criado_em=agora,
        expira_em=agora + timedelta(minutes=VALIDADE_MINUTOS),
        tentativas=0,
        validado=False,
    )
    db.session.add(codigo)
    db.session.commit()

    assunto, corpo = montar_email_de_codigo(
        usuario.nome_completo, codigo.codigo, VALIDADE_MINUTOS
    )
    try:
        enviado = enviar_email(usuario.email, assunto, corpo)
    except FalhaNoEnvio:
        # O codigo ja esta gravado e vale. Falha de SMTP nao pode derrubar o
        # cadastro - o usuario pede um reenvio.
        enviado = False

    return codigo, enviado


def validar_codigo(id_usuario, codigo_informado, finalidade="cadastro", agora=None):
    """Confere o codigo e, dando certo, ativa a conta.

    Cada tentativa errada incrementa o contador; na quinta, o codigo morre e
    e preciso pedir outro (RF10).
    """
    agora = agora or datetime.now()

    if not codigo_informado or not str(codigo_informado).strip():
        raise ErroDeValidacao("codigo", "Informe o codigo recebido.")

    usuario = db.session.get(Usuario, id_usuario)
    if usuario is None or usuario.status_conta == "excluido":
        raise NaoEncontrado(f"Usuario {id_usuario} nao encontrado.")

    registro = _ultimo_codigo(id_usuario, finalidade)
    if registro is None:
        raise ErroDeValidacao("codigo", "Nenhum codigo foi enviado. Peca um novo.")

    if registro.validado:
        raise ErroDeValidacao("codigo", "Este codigo ja foi utilizado. Peca um novo.")
    if registro.esgotou_tentativas():
        raise ErroDeValidacao(
            "codigo", "Numero de tentativas esgotado. Peca um novo codigo."
        )
    if registro.expirado(agora):
        raise ErroDeValidacao("codigo", "O codigo expirou. Peca um novo.")

    if str(codigo_informado).strip() != registro.codigo:
        registro.tentativas += 1
        db.session.commit()
        restantes = MAX_TENTATIVAS - registro.tentativas
        if restantes <= 0:
            raise ErroDeValidacao(
                "codigo", "Codigo incorreto. Tentativas esgotadas, peca um novo codigo."
            )
        raise ErroDeValidacao(
            "codigo", f"Codigo incorreto. Voce ainda tem {restantes} tentativa(s)."
        )

    registro.validado = True
    # RF11: e a validacao do codigo que tira a conta de 'pendente'.
    if usuario.status_conta == "pendente":
        usuario.status_conta = "ativo"
    db.session.commit()

    return usuario
