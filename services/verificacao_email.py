"""
Envio de código de verificação e notas fiscais em PDF por e-mail.
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from io import BytesIO
from weasyprint import HTML
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
    """Envia o código de verificação por e-mail."""
    if not servico_configurado():
        return False, "Envio de e-mail não está configurado no servidor."

    corpo_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #ea1d2c;">Yummy</h2>
        <p>Seu código de verificação é:</p>
        <p style="font-size: 32px; font-weight: bold; letter-spacing: 6px;">{codigo}</p>
        <p style="color: #777;">Esse código expira em 10 minutos. Não compartilhe com ninguém.</p>
    </div>
    """

    return _enviar_email(email_destino, f"{codigo} é o seu código de verificação Yummy", corpo_html)


def enviar_nota_fiscal(email_destino, html_nota, nome_cliente, id_pedido):
    """Gera o PDF da nota fiscal e envia como anexo no e-mail."""
    if not servico_configurado():
        return False, "Envio de e-mail não está configurado."

    # Corpo do e-mail
    corpo_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px; border-radius: 8px;">
        <h2 style="color: #ea1d2c; text-align: center;">Yummy</h2>
        <p>Olá, <strong>{nome_cliente}</strong>!</p>
        <p>Seu pedido <strong>#{id_pedido}</strong> foi entregue. Obrigado por comprar com a gente!</p>
        <p>Sua Nota Fiscal Eletrônica está em anexo neste e-mail.</p>
        <p style="color: #777; font-size: 12px; text-align: center; margin-top: 20px;">Este é um e-mail automático, não responda.</p>
    </div>
    """

    # Gerar o PDF a partir do HTML
    pdf_buffer = BytesIO()
    HTML(string=html_nota).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    # Montar o e-mail com o anexo
    msg = MIMEMultipart()
    msg["Subject"] = f"Sua Nota Fiscal - Pedido #{id_pedido} - Yummy"
    msg["From"] = f"{_REMETENTE_NOME} <{_SMTP_USER}>"
    msg["To"] = email_destino

    # Adiciona o corpo do e-mail
    msg.attach(MIMEText(corpo_html, "html"))

    # Adiciona o PDF como anexo
    anexo = MIMEApplication(pdf_buffer.read(), _subtype="pdf")
    anexo.add_header('Content-Disposition', f'attachment; filename="nota_fiscal_pedido_{id_pedido}.pdf"')
    msg.attach(anexo)

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=15) as servidor:
            servidor.starttls(context=contexto)
            servidor.login(_SMTP_USER, _SMTP_PASSWORD)
            servidor.sendmail(_SMTP_USER, [email_destino], msg.as_string())
        return True, None
    except Exception as e:
        return False, f"Não foi possível enviar o e-mail: {e}"


def _enviar_email(email_destino, assunto, corpo_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
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