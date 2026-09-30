from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import models
from controllers.decorators import login_requerido

cliente_bp = Blueprint("cliente", __name__, url_prefix="/cliente")


def _carrinho():
    carrinho = session.get("carrinho")
    if not isinstance(carrinho, dict) or "itens" not in carrinho or "id_restaurante" not in carrinho:
        session["carrinho"] = {"id_restaurante": None, "itens": {}}
        session.modified = True
    return session["carrinho"]


def _carrinho_totais(carrinho, desconto=0.0):
    subtotal = 0
    qtd_total = 0
    for item in carrinho.get("itens", {}).values():
        subtotal += item["preco"] * item["quantidade"]
        qtd_total += item["quantidade"]
    subtotal = round(subtotal, 2)
    desconto = round(float(desconto or 0), 2)
    total = round(max(subtotal - desconto, 0), 2)
    return {
        "subtotal": subtotal,
        "desconto": desconto,
        "total": total,
        "qtd_total": qtd_total,
    }


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
# ---------------------------------------------------------
@cliente_bp.route("/carrinho")
@login_requerido("cliente")
def ver_carrinho():
    carrinho = _carrinho()
    restaurante = None
    if carrinho.get("id_restaurante"):
        restaurante = models.buscar_restaurante(carrinho["id_restaurante"])
    if not restaurante:
        restaurante = {"nome_fantasia": "Nenhum restaurante selecionado", "foto_url": None}
    enderecos = models.listar_enderecos_cliente(session["user_id"])

    desconto = 0.0
    cupom_codigo = session.get("cupom")
    if cupom_codigo and carrinho.get("itens"):
        subtotal = _carrinho_totais(carrinho)["subtotal"]
        cupom, valor, erro = models.validar_cupom(
            cupom_codigo, session["user_id"], carrinho["id_restaurante"], subtotal
        )
        if erro:
            session.pop("cupom", None)
            session.modified = True
            cupom_codigo = None
        else:
            desconto = valor

    return render_template(
        "cliente/carrinho.html",
        carrinho=carrinho,
        totais=_carrinho_totais(carrinho, desconto),
        restaurante=restaurante,
        enderecos=enderecos,
        cupom_codigo=cupom_codigo,
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
            "foto_url": produto.get("foto_url"),
        }

    session.modified = True
    return jsonify({"ok": True, "carrinho": carrinho, "totais": _carrinho_totais(carrinho)})


@cliente_bp.route("/carrinho/limpar", methods=["POST"])
@login_requerido("cliente")
def limpar_carrinho():
    session["carrinho"] = {"id_restaurante": None, "itens": {}}
    session.pop("cupom", None)
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
        session.pop("cupom", None)

    session.modified = True

    desconto = 0.0
    cupom_codigo = session.get("cupom")
    if cupom_codigo and carrinho.get("itens"):
        subtotal = _carrinho_totais(carrinho)["subtotal"]
        cupom, valor, erro = models.validar_cupom(
            cupom_codigo, session["user_id"], carrinho["id_restaurante"], subtotal
        )
        if erro:
            session.pop("cupom", None)
            session.modified = True
        else:
            desconto = valor

    return jsonify({
        "ok": True,
        "carrinho": carrinho,
        "totais": _carrinho_totais(carrinho, desconto),
    })


# ---------------------------------------------------------
# CUPOM
# ---------------------------------------------------------
@cliente_bp.route("/carrinho/cupom", methods=["POST"])
@login_requerido("cliente")
def aplicar_cupom():
    dados = request.get_json() or {}
    codigo = (dados.get("codigo") or "").strip()
    carrinho = _carrinho()

    if not carrinho.get("itens"):
        return jsonify({"ok": False, "erro": "Seu carrinho está vazio."}), 400
    if not codigo:
        return jsonify({"ok": False, "erro": "Informe o código do cupom."}), 400

    subtotal = _carrinho_totais(carrinho)["subtotal"]
    cupom, valor, erro = models.validar_cupom(
        codigo, session["user_id"], carrinho["id_restaurante"], subtotal
    )
    if erro:
        return jsonify({"ok": False, "erro": erro}), 400

    session["cupom"] = codigo.upper()
    session.modified = True
    totais = _carrinho_totais(carrinho, valor)
    return jsonify({
        "ok": True,
        "cupom": codigo.upper(),
        "totais": totais,
        "descricao": cupom.get("descricao") or "",
    })


@cliente_bp.route("/carrinho/cupom/remover", methods=["POST"])
@login_requerido("cliente")
def remover_cupom():
    session.pop("cupom", None)
    session.modified = True
    carrinho = _carrinho()
    return jsonify({"ok": True, "totais": _carrinho_totais(carrinho)})


# ---------------------------------------------------------
# ENDEREÇO
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
        id_endereco = request.form.get("id_endereco")
        if not id_endereco:
            flash("Selecione um endereço de entrega.", "erro")
            return redirect(url_for("cliente.checkout"))

        itens = [
            {"id_produto": int(pid), "quantidade": item["quantidade"],
             "preco_unitario": item["preco"]}
            for pid, item in carrinho["itens"].items()
        ]
        try:
            id_pedido = models.criar_pedido_completo(
                id_cliente=session["user_id"],
                id_restaurante=carrinho["id_restaurante"],
                id_endereco=id_endereco,
                itens=itens,
                forma_pagamento=request.form["forma_pagamento"],
                codigo_cupom=session.get("cupom"),
            )
        except ValueError as e:
            flash(str(e), "erro")
            return redirect(url_for("cliente.ver_carrinho"))

        session["carrinho"] = {"id_restaurante": None, "itens": {}}
        session.pop("cupom", None)
        session.modified = True
        return redirect(url_for("cliente.pedido_sucesso", id_pedido=id_pedido))

    restaurante = None
    if carrinho.get("id_restaurante"):
        restaurante = models.buscar_restaurante(carrinho["id_restaurante"])
    if not restaurante:
        restaurante = {"nome_fantasia": "Nenhum restaurante selecionado"}

    enderecos = models.listar_enderecos_cliente(session["user_id"])

    desconto = 0.0
    cupom_codigo = session.get("cupom")
    if cupom_codigo:
        subtotal = _carrinho_totais(carrinho)["subtotal"]
        cupom, valor, erro = models.validar_cupom(
            cupom_codigo, session["user_id"], carrinho["id_restaurante"], subtotal
        )
        if erro:
            session.pop("cupom", None)
            cupom_codigo = None
            session.modified = True
        else:
            desconto = valor

    return render_template(
        "cliente/checkout.html",
        carrinho=carrinho,
        totais=_carrinho_totais(carrinho, desconto),
        restaurante=restaurante,
        enderecos=enderecos,
        cupom_codigo=cupom_codigo,
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
# API — PEDIDOS ATIVOS (usado pelo notificacoes.js)
# ---------------------------------------------------------
@cliente_bp.route("/api/pedidos-ativos")
@login_requerido("cliente")
def api_pedidos_ativos():
    pedidos = models.listar_pedidos_ativos_cliente(session["user_id"])
    return jsonify({
        "pedidos": [
            {
                "id": p["id"],
                "status": p["status"],
                "nome_fantasia": p["nome_fantasia"],
            }
            for p in pedidos
        ]
    })


# ---------------------------------------------------------
# PERFIL (com código de entrega)
# ---------------------------------------------------------
@cliente_bp.route("/perfil", methods=["GET", "POST"])
@login_requerido("cliente")
def editar_perfil():
    if request.method == "POST":
        models.atualizar_usuario(
            session["user_id"], request.form["nome"], request.form.get("telefone")
        )
        models.atualizar_cliente(session["user_id"], request.form.get("apelido"))

        codigo_entrega = (request.form.get("codigo_entrega") or "").strip()
        if codigo_entrega:
            if len(codigo_entrega) != 4 or not codigo_entrega.isdigit():
                flash("O código de entrega deve ter exatamente 4 dígitos.", "erro")
                return redirect(url_for("cliente.editar_perfil"))
            models.atualizar_codigo_entrega(session["user_id"], codigo_entrega)

        session["user_nome"] = request.form["nome"]
        flash("Perfil atualizado.", "sucesso")
        return redirect(url_for("cliente.editar_perfil"))

    cliente = models.buscar_cliente(session["user_id"])
    enderecos = models.listar_enderecos_cliente(session["user_id"])
    return render_template("cliente/editar_perfil.html", cliente=cliente, enderecos=enderecos)