import os
from datetime import timedelta
from flask import Flask, session
from dotenv import load_dotenv

from extensions import oauth
from controllers.home_ctrl import home_bp
from controllers.landing_ctrl import landing_bp
from controllers.auth_ctrl import auth_bp
from controllers.cliente_ctrl import cliente_bp
from controllers.restaurante_ctrl import restaurante_bp
from controllers.entregador_ctrl import entregador_bp
from controllers.pedido_ctrl import pedido_bp

load_dotenv()


def create_app():
    app = Flask(__name__)

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key or secret_key == "troque-esta-chave-em-producao":
        import secrets
        secret_key = secrets.token_urlsafe(64)
        print("[AVISO] SECRET_KEY não definida no .env. Sessões vão cair a cada restart.")
        print("[AVISO] Rode: python -c \"import secrets; print(secrets.token_urlsafe(64))\"")
        print("[AVISO] e cole o resultado no .env como SECRET_KEY=...")

    app.secret_key = secret_key

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_REFRESH_EACH_REQUEST=True,
    )

    oauth.init_app(app)

    app.register_blueprint(landing_bp)      # "/"
    app.register_blueprint(home_bp)         # "/cliente" (home do cliente)
    app.register_blueprint(auth_bp)         # "/auth"
    app.register_blueprint(cliente_bp)      # "/cliente/..."
    app.register_blueprint(restaurante_bp)  # "/restaurante/..."
    app.register_blueprint(entregador_bp)   # "/entregador/..."
    app.register_blueprint(pedido_bp)       # "/pedido/..."

    @app.context_processor
    def variaveis_globais():
        carrinho = session.get("carrinho", {"id_restaurante": None, "itens": {}})
        qtd_carrinho = sum(i["quantidade"] for i in carrinho.get("itens", {}).values())
        return {
            "logado": "user_id" in session,
            "user_tipo": session.get("user_tipo"),
            "user_nome": session.get("user_nome"),
            "qtd_carrinho": qtd_carrinho,
        }

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, port=5000)