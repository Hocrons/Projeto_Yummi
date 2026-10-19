import logging

import requests
from flask import Blueprint, jsonify, request

from services.geocoding import buscar_enderecos

logger = logging.getLogger(__name__)
geocoding_bp = Blueprint("geocoding", __name__)


@geocoding_bp.get("/api/geocoding/search")
def pesquisar_enderecos():
    query = (request.args.get("q") or "").strip()
    if len(query) < 3 or len(query) > 200:
        return jsonify({"ok": False, "erro": "Informe um endereço entre 3 e 200 caracteres."}), 400

    try:
        resultados = buscar_enderecos(query)
    except (requests.RequestException, ValueError):
        logger.exception("Falha ao consultar o serviço de geocodificação.")
        return jsonify({"ok": False, "erro": "Serviço de geocodificação indisponível."}), 503

    return jsonify({"ok": True, "resultados": resultados})
