"""
========================================================
  YUMMI — Endpoints REST para o App Android
  Adicione este arquivo como: controllers/mobile_api.py
  E registre no app.py: app.register_blueprint(mobile_api_bp)
========================================================
"""
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from models import models
import jwt
from datetime import datetime, timedelta

mobile_api_bp = Blueprint("mobile_api", __name__, url_prefix="/api/restaurante")

TOKEN_EXPIRY_HOURS = 24


# ─── helpers ────────────────────────────────────────────

def _make_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),  # PyJWT exige string
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, current_app.secret_key, algorithm="HS256")


def _decode_token(token: str):
    return jwt.decode(token, current_app.secret_key, algorithms=["HS256"])


def token_required(f):
    """Decorator: valida Bearer token e injeta user_id."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Token ausente."}), 401
        try:
            token_str = auth_header[7:]
            payload = _decode_token(token_str)
            user_id = int(payload["sub"])  # converte de volta para int
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Sessão expirada."}), 401
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            return jsonify({"success": False, "message": "Token inválido."}), 401
        return f(user_id, *args, **kwargs)
    return decorated


def _restaurante_json(r):
    return {
        "id": r["id_usuario"],
        "nome_fantasia": r["nome_fantasia"],
        "categoria": r["categoria"],
    }


def _produto_json(p):
    return {
        "id": p["id"],
        "id_restaurante": p["id_restaurante"],
        "nome": p["nome"],
        "descricao": p["descricao"],
        "preco": float(p["preco"]),
        "disponivel": bool(p["disponivel"]),
        "foto_url": p["foto_url"],
    }


# ─── rotas ──────────────────────────────────────────────

@mobile_api_bp.route("/login", methods=["POST"])
def login():
    """POST /api/restaurante/login  { email, senha }"""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    senha = data.get("senha") or ""

    if not email or not senha:
        return jsonify({"success": False, "message": "E-mail e senha obrigatórios."}), 400

    usuario = models.validar_login(email, senha, "restaurante")
    if not usuario:
        return jsonify({"success": False, "message": "E-mail ou senha inválidos."}), 401

    restaurante = models.buscar_restaurante(usuario["id"])
    if not restaurante:
        return jsonify({"success": False, "message": "Restaurante não encontrado."}), 404

    token = _make_token(usuario["id"])
    return jsonify({
        "success": True,
        "token": token,
        "restaurantId": usuario["id"],
        "nome": restaurante["nome_fantasia"],
    })


@mobile_api_bp.route("/produtos", methods=["GET"])
@token_required
def listar_produtos(user_id):
    """GET /api/restaurante/produtos  → lista de produtos do restaurante logado"""
    produtos = models.listar_produtos_restaurante(user_id)
    return jsonify({
        "success": True,
        "data": [_produto_json(p) for p in produtos],
    })


@mobile_api_bp.route("/produtos", methods=["POST"])
@token_required
def criar_produto(user_id):
    """POST /api/restaurante/produtos  { nome, descricao, preco, disponivel, foto_url }"""
    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    if not nome:
        return jsonify({"success": False, "message": "Nome obrigatório."}), 400

    try:
        preco = float(data.get("preco") or 0)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Preço inválido."}), 400

    produto_id = models.criar_produto(
        id_restaurante=user_id,
        nome=nome,
        descricao=(data.get("descricao") or "").strip() or None,
        preco=preco,
        disponivel=bool(data.get("disponivel", True)),
        foto_url=(data.get("foto_url") or "").strip() or None,
    )
    produto = models.buscar_produto(produto_id)
    return jsonify({"success": True, "data": _produto_json(produto)}), 201


@mobile_api_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
@token_required
def atualizar_produto(user_id, produto_id):
    """PUT /api/restaurante/produtos/:id"""
    produto = models.buscar_produto(produto_id)
    if not produto or produto["id_restaurante"] != user_id:
        return jsonify({"success": False, "message": "Produto não encontrado."}), 404

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    if not nome:
        return jsonify({"success": False, "message": "Nome obrigatório."}), 400

    try:
        preco = float(data.get("preco") or 0)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Preço inválido."}), 400

    models.atualizar_produto(
        produto_id=produto_id,
        nome=nome,
        descricao=(data.get("descricao") or "").strip() or None,
        preco=preco,
        disponivel=bool(data.get("disponivel", True)),
        foto_url=(data.get("foto_url") or "").strip() or None,
    )
    produto = models.buscar_produto(produto_id)
    return jsonify({"success": True, "data": _produto_json(produto)})


@mobile_api_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
@token_required
def deletar_produto(user_id, produto_id):
    """DELETE /api/restaurante/produtos/:id"""
    produto = models.buscar_produto(produto_id)
    if not produto or produto["id_restaurante"] != user_id:
        return jsonify({"success": False, "message": "Produto não encontrado."}), 404

    models.deletar_produto(produto_id)
    return jsonify({"success": True, "message": "Produto removido."})