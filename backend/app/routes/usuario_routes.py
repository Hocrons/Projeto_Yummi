"""Mapa de rotas do modulo de usuario.

Fica separado do controller para que a tabela de endpoints da API possa ser
lida de um arquivo so - util na documentacao da entrega.
"""
from flask import Blueprint

from app.controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")

usuario_bp.add_url_rule("", view_func=usuario_controller.criar, methods=["POST"])
usuario_bp.add_url_rule("", view_func=usuario_controller.listar, methods=["GET"])
usuario_bp.add_url_rule("/<int:id_usuario>", view_func=usuario_controller.buscar, methods=["GET"])
usuario_bp.add_url_rule(
    "/<int:id_usuario>", view_func=usuario_controller.atualizar, methods=["PATCH"]
)
usuario_bp.add_url_rule(
    "/<int:id_usuario>/status", view_func=usuario_controller.alterar_status, methods=["PATCH"]
)
usuario_bp.add_url_rule(
    "/<int:id_usuario>", view_func=usuario_controller.excluir, methods=["DELETE"]
)
