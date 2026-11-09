from flask import Blueprint, jsonify, render_template, request

from models import models
from services.periodos_relatorio import resolver_periodo_relatorio


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/relatorio")
def relatorio():
    try:
        periodo = resolver_periodo_relatorio(request.args, "mes")
    except ValueError as erro:
        return str(erro), 400

    dados = models.obter_relatorio_administrativo(
        periodo["data_inicio"], periodo["data_fim"]
    )
    return render_template("admin/relatorio.html", dados=dados, **periodo)


@admin_bp.route("/relatorio/dados")
def dados_relatorio():
    try:
        periodo = resolver_periodo_relatorio(request.args, "mes")
        dados = models.obter_relatorio_administrativo(
            periodo["data_inicio"], periodo["data_fim"]
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(dados), 200, {"Cache-Control": "no-store"}
