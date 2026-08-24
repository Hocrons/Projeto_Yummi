"""Mapa de rotas do codigo de verificacao."""
from flask import Blueprint

from app.controllers import otp_controller

otp_bp = Blueprint("verificacao", __name__, url_prefix="/api/verificacao")

otp_bp.add_url_rule("/enviar", view_func=otp_controller.enviar, methods=["POST"])
otp_bp.add_url_rule("/validar", view_func=otp_controller.validar, methods=["POST"])
