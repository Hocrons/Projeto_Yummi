from flask import Blueprint, jsonify, session
from models import models

pedido_bp = Blueprint("pedido", __name__, url_prefix="/pedido")


@pedido_bp.route("/<int:id_pedido>/status")
def status_pedido(id_pedido):
    """
    Endpoint simples de polling usado pelo JS da página de acompanhamento
    do pedido (ex.: templates/cliente/pedido_sucesso.html).
    """
    if "user_id" not in session:
        return jsonify({"erro": "não autenticado"}), 401

    pedido = models.buscar_pedido(id_pedido)
    if not pedido:
        return jsonify({"erro": "pedido não encontrado"}), 404

    return jsonify({
        "id": pedido["id"],
        "status": pedido["status"],
        "valor_total": float(pedido["valor_total"]),
    })
