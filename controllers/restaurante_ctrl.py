from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import models
from controllers.decorators import login_requerido

restaurante_bp = Blueprint("restaurante", __name__, url_prefix="/restaurante")


# ---------------------------------------------------------
# PAINEL (pedidos recebidos)
# ---------------------------------------------------------
@restaurante_bp.route("/painel")
@login_requerido("restaurante")
def painel():
    status = request.args.get("status")
    pedidos = models.listar_pedidos_restaurante(session["user_id"], status=status)
    return render_template("restaurante/painel.html", pedidos=pedidos, status_filtro=status)


@restaurante_bp.route("/pedido/<int:id_pedido>/status", methods=["POST"])
@login_requerido("restaurante")
def atualizar_status_pedido(id_pedido):
    novo_status = request.form["status"]
    permitido = {"pendente", "preparando", "pronto", "cancelado"}
    if novo_status in permitido:
        models.atualizar_status_pedido(id_pedido, novo_status)
        flash(f"Pedido #{id_pedido} atualizado para '{novo_status}'.", "sucesso")
    return redirect(url_for("restaurante.painel"))


# ---------------------------------------------------------
# CRUD DE PRODUTOS
# ---------------------------------------------------------
@restaurante_bp.route("/produtos")
@login_requerido("restaurante")
def produtos():
    lista = models.listar_produtos_por_restaurante(session["user_id"])
    return render_template("restaurante/produtos.html", produtos=lista)


@restaurante_bp.route("/produtos/novo", methods=["GET", "POST"])
@login_requerido("restaurante")
def produto_novo():
    if request.method == "POST":
        models.criar_produto(
            id_restaurante=session["user_id"],
            nome=request.form["nome"],
            descricao=request.form.get("descricao"),
            preco=request.form["preco"],
            disponivel=bool(request.form.get("disponivel")),
        )
        flash("Produto cadastrado.", "sucesso")
        return redirect(url_for("restaurante.produtos"))
    return render_template("restaurante/produto_novo.html")


@restaurante_bp.route("/produtos/<int:id_produto>/editar", methods=["GET", "POST"])
@login_requerido("restaurante")
def produto_editar(id_produto):
    produto = models.buscar_produto(id_produto)
    if not produto or produto["id_restaurante"] != session["user_id"]:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("restaurante.produtos"))

    if request.method == "POST":
        models.atualizar_produto(
            id_produto,
            nome=request.form["nome"],
            descricao=request.form.get("descricao"),
            preco=request.form["preco"],
            disponivel=bool(request.form.get("disponivel")),
        )
        flash("Produto atualizado.", "sucesso")
        return redirect(url_for("restaurante.produtos"))

    return render_template("restaurante/produto_editar.html", produto=produto)


@restaurante_bp.route("/produtos/<int:id_produto>/excluir", methods=["POST"])
@login_requerido("restaurante")
def produto_excluir(id_produto):
    produto = models.buscar_produto(id_produto)
    if produto and produto["id_restaurante"] == session["user_id"]:
        models.deletar_produto(id_produto)
        flash("Produto removido.", "sucesso")
    return redirect(url_for("restaurante.produtos"))


# ---------------------------------------------------------
# PERFIL
# ---------------------------------------------------------
@restaurante_bp.route("/perfil", methods=["GET", "POST"])
@login_requerido("restaurante")
def editar_perfil():
    if request.method == "POST":
        models.atualizar_usuario(
            session["user_id"], request.form["nome_responsavel"], request.form.get("telefone")
        )
        models.atualizar_restaurante(
            session["user_id"],
            nome_fantasia=request.form["nome_fantasia"],
            categoria=request.form.get("categoria"),
            taxa_entrega=request.form.get("taxa_entrega") or 0,
            horario_funcionamento=request.form.get("horario_funcionamento"),
            rua=request.form.get("rua"),
            numero=request.form.get("numero"),
            bairro=request.form.get("bairro"),
            cidade=request.form.get("cidade"),
            cep=request.form.get("cep"),
        )
        flash("Perfil do restaurante atualizado.", "sucesso")
        return redirect(url_for("restaurante.editar_perfil"))

    restaurante = models.buscar_restaurante(session["user_id"])
    return render_template("restaurante/editar_perfil.html", restaurante=restaurante)
