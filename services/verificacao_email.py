"""
Envio de código de verificação por e-mail, usado no fluxo "Entrar com e-mail".

Usa SMTP simples (funciona de graça com Gmail, usando uma "senha de app" -
não a senha normal da conta). Nenhuma biblioteca paga é necessária.
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

_SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USER = os.getenv("SMTP_USER")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
_REMETENTE_NOME = os.getenv("SMTP_REMETENTE_NOME", "Yummy")


def servico_configurado():
    return bool(_SMTP_USER and _SMTP_PASSWORD)


def enviar_codigo(email_destino, codigo):
    """
    Envia o código de verificação por e-mail.
    Retorna (sucesso: bool, mensagem_erro: str | None)
    """
    if not servico_configurado():
        return False, "Envio de e-mail não está configurado no servidor (faltam SMTP_USER / SMTP_PASSWORD no .env)."

    corpo_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #ea1d2c;">Yummy</h2>
        <p>Seu código de verificação é:</p>
        <p style="font-size: 32px; font-weight: bold; letter-spacing: 6px;">{codigo}</p>
        <p style="color: #777;">Esse código expira em 10 minutos. Não compartilhe com ninguém.</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{codigo} é o seu código de verificação Yummy"
    msg["From"] = f"{_REMETENTE_NOME} <{_SMTP_USER}>"
    msg["To"] = email_destino
    msg.attach(MIMEText(corpo_html, "html"))

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as servidor:
            servidor.starttls(context=contexto)
            servidor.login(_SMTP_USER, _SMTP_PASSWORD)
            servidor.sendmail(_SMTP_USER, [email_destino], msg.as_string())
        return True, None
    except Exception as e:
        return False, f"Não foi possível enviar o e-mail: {e}"