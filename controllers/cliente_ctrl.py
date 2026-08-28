from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import models
from controllers.decorators import login_requerido

cliente_bp = Blueprint("cliente", __name__, url_prefix="/cliente")


def _carrinho():
    """Garante que o carrinho existe na sessão e auto-repara a estrutura se estiver corrompida."""
    carrinho = session.get("carrinho")

    if not isinstance(carrinho, dict) or "itens" not in carrinho or "id_restaurante" not in carrinho:
        session["carrinho"] = {"id_restaurante": None, "itens": {}}
        session.modified = True

    return session["carrinho"]


def _carrinho_totais(carrinho):
    total = 0
    qtd_total = 0
    itens = carrinho.get("itens", {})
    for item in itens.values():
        total += item["preco"] * item["quantidade"]
        qtd_total += item["quantidade"]
    return {"total": round(total, 2), "qtd_total": qtd_total}


# ---------------------------------------------------------
# CARDÁPIO
# ---------------------------------------------------------
@cliente_bp.route("/restaurante/<int:id_restaurante>")
def ver_cardapio(id_restaurante):
    restaurante = models.buscar_restaurante(id_restaurante)
    if not restaurante:
        flash("Restaurante não encontrado.", "erro")
        return redirect(url_for("home.index"))
    produtos = models.listar_produtos_por_restaurante(id_restaurante, apenas_disponiveis=True)
    return render_template("cliente/ver_cardapio.html", restaurante=restaurante, produtos=produtos)


# ---------------------------------------------------------
# CARRINHO
# (a regra de "só um restaurante por carrinho" é aplicada aqui E de novo
#  no models.criar_pedido_completo, como segunda camada de proteção)
# ---------------------------------------------------------
@cliente_bp.route("/carrinho")
@login_requerido("cliente")
def ver_carrinho():
    carrinho = _carrinho()
    restaurante = None

    if carrinho.get("id_restaurante"):
        restaurante = models.buscar_restaurante(carrinho["id_restaurante"])

    if not restaurante:
        restaurante = {"nome_fantasia": "Nenhum restaurante selecionado"}

    enderecos = models.listar_enderecos_cliente(session["user_id"])
    return render_template(
        "cliente/carrinho.html",
        carrinho=carrinho,
        totais=_carrinho_totais(carrinho),
        restaurante=restaurante,
        enderecos=enderecos,
    )


@cliente_bp.route("/carrinho/adicionar", methods=["POST"])
@login_requerido("cliente")
def adicionar_ao_carrinho():
    dados = request.get_json()
    if not dados or "id_produto" not in dados:
        return jsonify({"erro": "Dados inválidos."}), 400

    produto = models.buscar_produto(dados["id_produto"])
    if not produto or not produto.get("disponivel"):
        return jsonify({"erro": "Produto indisponível."}), 400

    carrinho = _carrinho()

    # Regra iFood: impede adicionar itens de restaurantes diferentes no mesmo carrinho
    if carrinho.get("itens") and carrinho.get("id_restaurante") != produto["id_restaurante"]:
        return jsonify({
            "erro": "Seu carrinho já tem itens de outro restaurante.",
            "conflito_restaurante": True,
        }), 409

    carrinho["id_restaurante"] = produto["id_restaurante"]
    pid = str(produto["id"])

    if pid in carrinho["itens"]:
        carrinho["itens"][pid]["quantidade"] += 1
    else:
        carrinho["itens"][pid] = {
            "nome": produto["nome"],
            "preco": float(produto["preco"]),
            "quantidade": 1,
        }

    session.modified = True
    return jsonify({"ok": True, "carrinho": carrinho, "totais": _carrinho_totais(carrinho)})


@cliente_bp.route("/carrinho/limpar", methods=["POST"])
@login_requerido("cliente")
def limpar_carrinho():
    session["carrinho"] = {"id_restaurante": None, "itens": {}}
    session.modified = True
    return jsonify({"ok": True})


@cliente_bp.route("/carrinho/atualizar", methods=["POST"])
@login_requerido("cliente")
def atualizar_carrinho():
    dados = request.get_json()
    pid = str(dados["id_produto"])
    quantidade = int(dados["quantidade"])
    carrinho = _carrinho()

    if pid in carrinho.get("itens", {}):
        if quantidade <= 0:
            del carrinho["itens"][pid]
        else:
            carrinho["itens"][pid]["quantidade"] = quantidade

    if not carrinho.get("itens"):
        carrinho["id_restaurante"] = None

    session.modified = True
    return jsonify({"ok": True, "carrinho": carrinho, "totais": _carrinho_totais(carrinho)})


# ---------------------------------------------------------
# ENDEREÇO - CRUD completo, usado tanto no perfil quanto no checkout
# ---------------------------------------------------------
@cliente_bp.route("/endereco/adicionar", methods=["POST"])
@login_requerido("cliente")
def adicionar_endereco():
    models.criar_endereco(
        id_cliente=session["user_id"],
        rua=request.form["rua"],
        numero=request.form.get("numero"),
        bairro=request.form.get("bairro"),
        cidade=request.form.get("cidade"),
        cep=request.form.get("cep"),
    )
    flash("Endereço adicionado.", "sucesso")

    # 'origem' define para onde voltar depois de salvar (perfil ou checkout)
    if request.form.get("origem") == "perfil":
        return redirect(url_for("cliente.editar_perfil"))
    return redirect(url_for("cliente.ver_carrinho"))


@cliente_bp.route("/endereco/<int:id_endereco>/editar", methods=["GET", "POST"])
@login_requerido("cliente")
def editar_endereco(id_endereco):
    endereco = models.buscar_endereco(id_endereco)
    if not endereco or endereco["id_cliente"] != session["user_id"]:
        flash("Endereço não encontrado.", "erro")
        return redirect(url_for("cliente.editar_perfil"))

    if request.method == "POST":
        models.atualizar_endereco(
            id_endereco,
            id_cliente=session["user_id"],
            rua=request.form["rua"],
            numero=request.form.get("numero"),
            bairro=request.form.get("bairro"),
            cidade=request.form.get("cidade"),
            cep=request.form.get("cep"),
        )
        flash("Endereço atualizado.", "sucesso")
        return redirect(url_for("cliente.editar_perfil"))

    return render_template("cliente/editar_endereco.html", endereco=endereco)


@cliente_bp.route("/endereco/<int:id_endereco>/excluir", methods=["POST"])
@login_requerido("cliente")
def excluir_endereco(id_endereco):
    sucesso = models.deletar_endereco(id_endereco, session["user_id"])
    if sucesso:
        flash("Endereço removido.", "sucesso")
    else:
        flash("Não foi possível remover esse endereço.", "erro")
    return redirect(url_for("cliente.editar_perfil"))


# ---------------------------------------------------------
# CHECKOUT
# ---------------------------------------------------------
@cliente_bp.route("/checkout", methods=["GET", "POST"])
@login_requerido("cliente")
def checkout():
    carrinho = _carrinho()
    if not carrinho.get("itens"):
        flash("Seu carrinho está vazio.", "erro")
        return redirect(url_for("home.index"))

    if request.method == "POST":
        itens = [
            {"id_produto": int(pid), "quantidade": item["quantidade"], "preco_unitario": item["preco"]}
            for pid, item in carrinho["itens"].items()
        ]
        try:
            id_pedido = models.criar_pedido_completo(
                id_cliente=session["user_id"],
                id_restaurante=carrinho["id_restaurante"],
                id_endereco=request.form.get("id_endereco") or None,
                itens=itens,
                forma_pagamento=request.form["forma_pagamento"],
            )
        except ValueError as e:
            # Ex: itens de restaurantes diferentes, produto removido, etc.
            flash(str(e), "erro")
            return redirect(url_for("cliente.ver_carrinho"))

        session["carrinho"] = {"id_restaurante": None, "itens": {}}
        session.modified = True
        return redirect(url_for("cliente.pedido_sucesso", id_pedido=id_pedido))

    restaurante = None
    if carrinho.get("id_restaurante"):
        restaurante = models.buscar_restaurante(carrinho["id_restaurante"])

    if not restaurante:
        restaurante = {"nome_fantasia": "Nenhum restaurante selecionado"}

    enderecos = models.listar_enderecos_cliente(session["user_id"])
    return render_template(
        "cliente/checkout.html",
        carrinho=carrinho,
        totais=_carrinho_totais(carrinho),
        restaurante=restaurante,
        enderecos=enderecos,
    )


@cliente_bp.route("/pedido/<int:id_pedido>/sucesso")
@login_requerido("cliente")
def pedido_sucesso(id_pedido):
    pedido = models.buscar_pedido(id_pedido)
    return render_template("cliente/pedido_sucesso.html", pedido=pedido)


# ---------------------------------------------------------
# MEUS PEDIDOS
# ---------------------------------------------------------
@cliente_bp.route("/pedidos")
@login_requerido("cliente")
def meus_pedidos():
    pedidos = models.listar_pedidos_cliente(session["user_id"])
    return render_template("cliente/meus_pedidos.html", pedidos=pedidos)


# ---------------------------------------------------------
# PERFIL
# ---------------------------------------------------------
@cliente_bp.route("/perfil", methods=["GET", "POST"])
@login_requerido("cliente")
def editar_perfil():
    if request.method == "POST":
        models.atualizar_usuario(
            session["user_id"], request.form["nome"], request.form.get("telefone")
        )
        models.atualizar_cliente(session["user_id"], request.form.get("apelido"))
        session["user_nome"] = request.form["nome"]
        flash("Perfil atualizado.", "sucesso")
        return redirect(url_for("cliente.editar_perfil"))

    cliente = models.buscar_cliente(session["user_id"])
    enderecos = models.listar_enderecos_cliente(session["user_id"])
    return render_template("cliente/editar_perfil.html", cliente=cliente, enderecos=enderecos)