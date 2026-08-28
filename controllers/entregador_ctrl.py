from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import models
from controllers.decorators import login_requerido

entregador_bp = Blueprint("entregador", __name__, url_prefix="/entregador")


@entregador_bp.route("/painel")
@login_requerido("entregador")
def painel():
    entregador = models.buscar_entregador(session["user_id"])
    disponiveis = models.listar_pedidos_disponiveis_para_entrega()
    minhas_entregas = models.listar_pedidos_entregador(session["user_id"])
    return render_template(
        "entregador/painel.html",
        entregador=entregador,
        disponiveis=disponiveis,
        minhas_entregas=minhas_entregas,
    )


@entregador_bp.route("/disponibilidade", methods=["POST"])
@login_requerido("entregador")
def alternar_disponibilidade():
    entregador = models.buscar_entregador(session["user_id"])
    novo_status = not entregador["disponivel"]
    models.atualizar_disponibilidade_entregador(session["user_id"], novo_status)
    return redirect(url_for("entregador.painel"))


@entregador_bp.route("/pedido/<int:id_pedido>/aceitar", methods=["POST"])
@login_requerido("entregador")
def aceitar_pedido(id_pedido):
    """Entregador aceita a corrida -> status vai para 'indo_ao_restaurante'."""
    sucesso = models.atribuir_entregador(id_pedido, session["user_id"])
    if sucesso:
        flash(f"Pedido #{id_pedido} aceito! Vá até o restaurante para retirar.", "sucesso")
    else:
        flash("Esse pedido já foi aceito por outro entregador ou não está mais disponível.", "erro")
    return redirect(url_for("entregador.painel"))


@entregador_bp.route("/pedido/<int:id_pedido>/retirado", methods=["POST"])
@login_requerido("entregador")
def marcar_retirado(id_pedido):
    """Entregador confirma que retirou o pedido no restaurante -> 'saiu_para_entrega'."""
    sucesso = models.marcar_pedido_retirado(id_pedido, session["user_id"])
    if sucesso:
        flash(f"Pedido #{id_pedido} retirado. Bora entregar!", "sucesso")
    else:
        flash("Não foi possível atualizar esse pedido.", "erro")
    return redirect(url_for("entregador.painel"))


@entregador_bp.route("/pedido/<int:id_pedido>/entregue", methods=["POST"])
@login_requerido("entregador")
def marcar_entregue(id_pedido):
    """Entregador confirma a entrega -> 'entregue' + pagamento aprovado."""
    sucesso = models.marcar_pedido_entregue(id_pedido, session["user_id"])
    if sucesso:
        models.atualizar_status_pagamento(id_pedido, "aprovado")
        flash(f"Pedido #{id_pedido} marcado como entregue.", "sucesso")
    else:
        flash("Não foi possível concluir esse pedido.", "erro")
    return redirect(url_for("entregador.painel"))