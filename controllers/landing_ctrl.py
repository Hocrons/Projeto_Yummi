"""
Controller da landing page inicial.
Apresenta os 3 portais (cliente, restaurante, entregador)
e direciona cada um para o seu fluxo.
"""
from flask import Blueprint, render_template

landing_bp = Blueprint("landing", __name__)


@landing_bp.route("/")
def index():
    return render_template("landing/index.html")