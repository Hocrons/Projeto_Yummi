"""Fixtures compartilhadas dos testes.

Os testes rodam contra SQLite em memoria: sobem e caem em segundos e nao
exigem MySQL instalado na maquina de quem for rodar. As regras de negocio
testadas aqui vivem no servico, entao independem do dialeto do banco.
"""
import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db

# CPFs com digitos verificadores validos, gerados pelo proprio algoritmo.
CPF_VALIDO = "52998224725"
CPF_VALIDO_2 = "16899535009"
CPF_INVALIDO = "52998224724"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def usuario_valido():
    """Corpo minimo de um cadastro que deve passar em todas as validacoes."""
    return {
        "nome_completo": "Maria de Souza",
        "email": "maria@exemplo.com",
        "celular": "11987654321",
        "cpf": CPF_VALIDO,
        "data_nascimento": "1998-03-15",
        "senha": "senhaSegura123",
    }
