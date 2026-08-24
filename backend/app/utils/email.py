"""Envio de e-mail por SMTP, com queda para o console.

Usa apenas a biblioteca padrao (smtplib), sem dependencia nova.

Quando SMTP_USER e SMTP_PASSWORD nao estao no .env, o e-mail nao e enviado:
o conteudo aparece no log do backend. Isso mantem o projeto rodando na maquina
de quem ainda nao configurou credencial, sem quebrar o cadastro.
"""
import smtplib
from email.message import EmailMessage

from flask import current_app


class FalhaNoEnvio(Exception):
    """O servidor SMTP recusou ou nao respondeu."""


def _configurado():
    cfg = current_app.config
    return bool(cfg.get("SMTP_USER") and cfg.get("SMTP_PASSWORD"))


def _imprimir_no_console(destinatario, assunto, corpo):
    """Modo de desenvolvimento: mostra o e-mail no log em vez de enviar."""
    current_app.logger.info(
        "\n"
        "+---------------- E-MAIL (nao enviado) ----------------+\n"
        " Para:    %s\n"
        " Assunto: %s\n"
        "\n%s\n"
        "+------------------------------------------------------+\n"
        " Configure SMTP_USER e SMTP_PASSWORD no .env para enviar de verdade.\n",
        destinatario, assunto, corpo,
    )


def enviar_email(destinatario, assunto, corpo):
    """Envia o e-mail. Devolve True se saiu pelo SMTP, False se foi para o log.

    Levanta FalhaNoEnvio quando ha credencial configurada mas o envio falha -
    quem chama decide se isso derruba a operacao ou nao.
    """
    if not _configurado():
        _imprimir_no_console(destinatario, assunto, corpo)
        return False

    cfg = current_app.config
    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = cfg.get("SMTP_FROM") or cfg["SMTP_USER"]
    mensagem["To"] = destinatario
    mensagem.set_content(corpo)

    try:
        with smtplib.SMTP(cfg["SMTP_HOST"], int(cfg["SMTP_PORT"]), timeout=15) as servidor:
            servidor.starttls()
            servidor.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            servidor.send_message(mensagem)
    except (smtplib.SMTPException, OSError) as erro:
        # Nao registra o endereco: RNF04 mantem dado pessoal fora do log.
        current_app.logger.error("Falha ao enviar e-mail: %s", erro)
        raise FalhaNoEnvio(str(erro)) from erro

    current_app.logger.info("E-mail enviado com assunto %r.", assunto)
    return True


def montar_email_de_codigo(nome, codigo, validade_minutos):
    """Texto do e-mail com o codigo de verificacao."""
    assunto = f"{codigo} e o seu codigo de verificacao do Yummi"
    corpo = (
        f"Ola, {nome}!\n\n"
        f"Seu codigo de verificacao do Yummi e:\n\n"
        f"    {codigo}\n\n"
        f"Ele vale por {validade_minutos} minutos.\n\n"
        "Se nao foi voce que pediu este codigo, ignore este e-mail.\n\n"
        "-- \nEquipe Yummi"
    )
    return assunto, corpo
