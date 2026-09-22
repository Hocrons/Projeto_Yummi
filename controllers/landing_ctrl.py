"""
Controller da landing page inicial.
Apresenta os 3 portais (cliente, restaurante, entregador)
e direciona cada um para o seu fluxo.
"""
from flask import Blueprint, render_template, redirect, url_for, session

landing_bp = Blueprint("landing", __name__)


@landing_bp.route("/")
def index():
    return render_template("landing/index.html")


@landing_bp.route("/escolher-portal")
def escolher_portal():
    """
    Endpoint usado pelo botão "Escolha seu portal" na navbar dos 3 portais.
    Faz logout e volta pra landing, garantindo que o usuário não carregue
    sessão de um portal para outro.
    """
    session.clear()
    return redirect(url_for("landing.index"))