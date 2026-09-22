from flask import Blueprint, render_template, request
from models import models

home_bp = Blueprint("home", __name__, url_prefix="/cliente")


@home_bp.route("")
@home_bp.route("/")
def index():
    categoria = request.args.get("categoria")
    busca = (request.args.get("busca") or "").strip()

    # Aba ativa: "lojas" (padrão) ou "itens" (só faz sentido se houver busca)
    aba = request.args.get("aba") or "lojas"
    if aba not in ("lojas", "itens"):
        aba = "lojas"

    restaurantes = models.listar_restaurantes(categoria=categoria, busca=busca or None)
    categorias = models.listar_categorias()

    # Só busca produtos se houver termo digitado
    produtos = []
    if busca:
        produtos = models.buscar_produtos_por_nome(busca)

    return render_template(
        "index.html",
        restaurantes=restaurantes,
        categorias=categorias,
        categoria_selecionada=categoria,
        busca=busca,
        produtos=produtos,
        aba=aba,
    )