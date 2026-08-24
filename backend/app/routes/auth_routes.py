"""Mapa de rotas de autenticacao."""
from flask import Blueprint

from app.controllers import auth_controller

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

auth_bp.add_url_rule("/login", view_func=auth_controller.login, methods=["POST"])
