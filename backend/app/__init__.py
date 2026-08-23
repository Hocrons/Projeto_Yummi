"""Fabrica da aplicacao Flask.

Concentra o registro de extensoes, blueprints e tratadores de erro. Receber a
config por parametro e o que permite os testes subirem a app apontando para o
banco em memoria sem tocar no ambiente de desenvolvimento.
"""
import logging

from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError

from app.config import Config
from app.docs import init_swagger
from app.extensions import db
from app.utils.errors import ErroDeConflito, ErroDeValidacao, NaoEncontrado
from flask_cors import CORS


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})
    # Importado aqui (e nao no topo) para registrar as tabelas no metadata
    # somente depois que o db existe.
    from app import models  # noqa: F401
    from app.routes.usuario_routes import usuario_bp

    app.register_blueprint(usuario_bp)

    init_swagger(app)
    _registrar_logs(app)
    _registrar_tratadores_de_erro(app)

    @app.get("/api/saude")
    def saude():
        """Confere se a API subiu.
        ---
        tags: [Servico]
        responses:
          200:
            description: API no ar.
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    status: {type: string, example: ok}
                    servico: {type: string, example: yummi-api}
        """
        return jsonify({"status": "ok", "servico": "yummi-api"}), 200

    return app


def _registrar_logs(app):
    """RNF10: erros e acoes ficam visiveis no console durante o desenvolvimento."""
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s em %(module)s: %(message)s")
        )
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def _registrar_tratadores_de_erro(app):
    """Traduz excecao de negocio em status HTTP, com corpo de erro padronizado."""

    @app.errorhandler(ErroDeValidacao)
    def _validacao(erro):
        app.logger.info("Validacao falhou em %s: %s", erro.campo, erro.mensagem)
        return jsonify({"erro": {"campo": erro.campo, "mensagem": erro.mensagem}}), 400

    @app.errorhandler(ErroDeConflito)
    def _conflito(erro):
        app.logger.info("Conflito de unicidade em %s: %s", erro.campo, erro.mensagem)
        return jsonify({"erro": {"campo": erro.campo, "mensagem": erro.mensagem}}), 409

    @app.errorhandler(NaoEncontrado)
    def _nao_encontrado(erro):
        return jsonify({"erro": {"mensagem": str(erro)}}), 404

    @app.errorhandler(IntegrityError)
    def _integridade(erro):
        # Rede de seguranca: se duas requisicoes simultaneas passarem pela
        # checagem de unicidade do servico, o UNIQUE do banco ainda barra.
        db.session.rollback()
        app.logger.warning("Integridade violada no banco: %s", erro.orig)
        return jsonify({
            "erro": {"mensagem": "A operacao viola uma restricao de integridade do banco."}
        }), 409

    @app.errorhandler(404)
    def _rota_inexistente(_):
        return jsonify({"erro": {"mensagem": "Rota nao encontrada."}}), 404

    @app.errorhandler(405)
    def _metodo_invalido(_):
        return jsonify({"erro": {"mensagem": "Metodo nao permitido para esta rota."}}), 405

    @app.errorhandler(Exception)
    def _erro_inesperado(erro):
        db.session.rollback()
        app.logger.exception("Erro nao tratado: %s", erro)
        return jsonify({"erro": {"mensagem": "Erro interno no servidor."}}), 500
