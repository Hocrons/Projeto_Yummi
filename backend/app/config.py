"""Configuracao da aplicacao, lida de variaveis de ambiente (.env)."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Credenciais nunca ficam no codigo (RNF04 - seguranca de dados).
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "yummi")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
    JSON_SORT_KEYS = False

    # Envio de e-mail. Sem SMTP_USER e SMTP_PASSWORD, o codigo de verificacao
    # aparece no log do backend em vez de ser enviado (ver utils/email.py).
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = os.getenv("SMTP_PORT", "587")
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")


class TestConfig(Config):
    """Banco em memoria, usado pelos testes automatizados."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"

    # Zerado de proposito: sem credencial, utils/email.py cai no modo console.
    # Sem isto, um .env com SMTP configurado faria a suite disparar e-mail de
    # verdade a cada execucao.
    SMTP_USER = ""
    SMTP_PASSWORD = ""
