from flask import Blueprint, render_template, request
from models import models

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    categoria = request.args.get("categoria")
    busca = request.args.get("busca")
    restaurantes = models.listar_restaurantes(categoria=categoria, busca=busca)
    categorias = models.listar_categorias()
    return render_template(
        "index.html",
        restaurantes=restaurantes,
        categorias=categorias,
        categoria_selecionada=categoria,
        busca=busca or "",
    )
