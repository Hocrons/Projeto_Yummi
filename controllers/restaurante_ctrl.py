from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import models
from controllers.decorators import login_requerido

restaurante_bp = Blueprint("restaurante", __name__, url_prefix="/restaurante")

TRANSICOES_PERMITIDAS = {
    "pendente": ["preparando", "cancelado"],
    "preparando": ["localizando_entregador", "cancelado"],
}


def _url_valida(url):
    """Aceita só http:// ou https://. Vazio vira None. Inválido vira False."""
    url = (url or "").strip()
    if not url:
        return None
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    if len(url) > 500:
        return False
    return url


# ---------------------------------------------------------
# PORTAL (ponto de entrada)
# ---------------------------------------------------------
@restaurante_bp.route("")
@restaurante_bp.route("/")
def portal():
    if session.get("user_tipo") == "restaurante":
        return redirect(url_for("restaurante.painel"))
    return redirect(url_for("auth.login_restaurante"))


# ---------------------------------------------------------
# PAINEL
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
    pedido = models.buscar_pedido(id_pedido)

    if not pedido or pedido["id_restaurante"] != session["user_id"]:
        flash("Pedido não encontrado.", "erro")
        return redirect(url_for("restaurante.painel"))

    permitidos = TRANSICOES_PERMITIDAS.get(pedido["status"], [])
    if novo_status not in permitidos:
        flash("Essa mudança de status não é permitida neste momento.", "erro")
        return redirect(url_for("restaurante.painel"))

    models.atualizar_status_pedido(id_pedido, novo_status, id_restaurante=session["user_id"])
    flash(f"Pedido #{id_pedido} atualizado para '{novo_status}'.", "sucesso")
    return redirect(url_for("restaurante.painel"))


@restaurante_bp.route("/pedido/<int:id_pedido>/trocar-entregador", methods=["POST"])
@login_requerido("restaurante")
def trocar_entregador(id_pedido):
    sucesso = models.liberar_entregador(id_pedido, session["user_id"])
    if sucesso:
        flash(f"Pedido #{id_pedido}: buscando um novo entregador.", "sucesso")
    else:
        flash("Não é possível trocar o entregador neste momento (ele já pode ter retirado o pedido).", "erro")
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
        foto_url = _url_valida(request.form.get("foto_url"))
        if foto_url is False:
            flash("URL da foto inválida. Use http:// ou https://", "erro")
            return render_template("restaurante/produto_novo.html", form=request.form)

        models.criar_produto(
            id_restaurante=session["user_id"],
            nome=request.form["nome"],
            descricao=request.form.get("descricao"),
            preco=request.form["preco"],
            disponivel=bool(request.form.get("disponivel")),
            foto_url=foto_url,
        )
        flash("Produto cadastrado.", "sucesso")
        return redirect(url_for("restaurante.produtos"))
    return render_template("restaurante/produto_novo.html", form={})


@restaurante_bp.route("/produtos/<int:id_produto>/editar", methods=["GET", "POST"])
@login_requerido("restaurante")
def produto_editar(id_produto):
    produto = models.buscar_produto(id_produto)
    if not produto or produto["id_restaurante"] != session["user_id"]:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("restaurante.produtos"))

    if request.method == "POST":
        foto_url = _url_valida(request.form.get("foto_url"))
        if foto_url is False:
            flash("URL da foto inválida. Use http:// ou https://", "erro")
            return render_template("restaurante/produto_editar.html", produto=produto)

        models.atualizar_produto(
            id_produto,
            nome=request.form["nome"],
            descricao=request.form.get("descricao"),
            preco=request.form["preco"],
            disponivel=bool(request.form.get("disponivel")),
            foto_url=foto_url,
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
# CRUD DE CUPONS
# ---------------------------------------------------------
def _parse_decimal(valor):
    """Converte string de formulário pra float. Retorna None se vazio."""
    if valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _parse_int(valor):
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None


def _parse_datetime(valor):
    """Campo datetime-local vem como 'YYYY-MM-DDTHH:MM'. Retorna string aceita pelo MySQL."""
    if not valor:
        return None
    valor = valor.strip().replace("T", " ")
    if len(valor) == 16:  # sem segundos
        valor += ":00"
    return valor


def _validar_form_cupom(form):
    """Valida o form. Retorna (dados, erro_msg)."""
    codigo = (form.get("codigo") or "").strip().upper()
    if not codigo:
        return None, "Informe o código do cupom."
    if len(codigo) > 30:
        return None, "O código pode ter no máximo 30 caracteres."
    if not codigo.replace("-", "").replace("_", "").isalnum():
        return None, "O código só pode ter letras, números, hífen e underline."

    tipo = form.get("tipo")
    if tipo not in ("percentual", "fixo"):
        return None, "Escolha o tipo de desconto."

    valor = _parse_decimal(form.get("valor"))
    if valor is None or valor <= 0:
        return None, "Informe um valor de desconto maior que zero."

    if tipo == "percentual" and valor > 100:
        return None, "Um desconto percentual não pode passar de 100%."

    valor_minimo = _parse_decimal(form.get("valor_minimo_pedido")) or 0
    if valor_minimo < 0:
        return None, "O valor mínimo do pedido não pode ser negativo."

    valor_maximo = _parse_decimal(form.get("valor_maximo_desconto"))
    if valor_maximo is not None and valor_maximo < 0:
        return None, "O teto de desconto não pode ser negativo."

    data_inicio = _parse_datetime(form.get("data_inicio"))
    data_fim = _parse_datetime(form.get("data_fim"))
    if data_inicio and data_fim and data_fim < data_inicio:
        return None, "A data final não pode ser antes da data inicial."

    limite_total = _parse_int(form.get("limite_usos_total"))
    if limite_total is not None and limite_total <= 0:
        return None, "O limite total de usos precisa ser maior que zero (ou vazio pra ilimitado)."

    limite_cliente = _parse_int(form.get("limite_usos_por_cliente"))
    if limite_cliente is not None and limite_cliente <= 0:
        return None, "O limite por cliente precisa ser maior que zero (ou vazio pra ilimitado)."

    return {
        "codigo": codigo,
        "descricao": (form.get("descricao") or "").strip() or None,
        "tipo": tipo,
        "valor": valor,
        "valor_minimo_pedido": valor_minimo,
        "valor_maximo_desconto": valor_maximo,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "limite_usos_total": limite_total,
        "limite_usos_por_cliente": limite_cliente,
        "ativo": bool(form.get("ativo")),
    }, None


def _calcular_status_cupom(c):
    """
    Retorna (label, classe_css) do status atual do cupom.
    Classes: ativo | inativo | expirado | agendado | esgotado
    """
    from datetime import datetime
    agora = datetime.now()

    if not c["ativo"]:
        return "Inativo", "inativo"
    if c["data_inicio"] and agora < c["data_inicio"]:
        return "Agendado", "agendado"
    if c["data_fim"] and agora > c["data_fim"]:
        return "Expirado", "expirado"
    if c["limite_usos_total"] is not None and c["usos_atuais"] >= c["limite_usos_total"]:
        return "Esgotado", "esgotado"
    return "Ativo", "ativo"


@restaurante_bp.route("/cupons")
@login_requerido("restaurante")
def cupons():
    lista = models.listar_cupons(id_restaurante=session["user_id"], apenas_ativos=False)

    # Enriquece cada cupom com status calculado
    for c in lista:
        label, classe = _calcular_status_cupom(c)
        c["status_label"] = label
        c["status_classe"] = classe

    return render_template("restaurante/cupons.html", cupons=lista)


@restaurante_bp.route("/cupons/novo", methods=["GET", "POST"])
@login_requerido("restaurante")
def cupom_novo():
    if request.method == "POST":
        dados, erro = _validar_form_cupom(request.form)
        if erro:
            flash(erro, "erro")
            return render_template("restaurante/cupom_form.html", cupom=None, form=request.form)

        # Código único globalmente (a coluna tem UNIQUE)
        if models.buscar_cupom_por_codigo(dados["codigo"]):
            flash(f"Já existe um cupom com o código '{dados['codigo']}'.", "erro")
            return render_template("restaurante/cupom_form.html", cupom=None, form=request.form)

        try:
            models.criar_cupom(
                codigo=dados["codigo"],
                descricao=dados["descricao"],
                tipo=dados["tipo"],
                valor=dados["valor"],
                valor_minimo_pedido=dados["valor_minimo_pedido"],
                valor_maximo_desconto=dados["valor_maximo_desconto"],
                data_inicio=dados["data_inicio"],
                data_fim=dados["data_fim"],
                limite_usos_total=dados["limite_usos_total"],
                limite_usos_por_cliente=dados["limite_usos_por_cliente"],
                id_restaurante=session["user_id"],
                ativo=dados["ativo"],
            )
        except Exception as e:
            flash(f"Erro ao criar cupom: {e}", "erro")
            return render_template("restaurante/cupom_form.html", cupom=None, form=request.form)

        flash(f"Cupom '{dados['codigo']}' criado!", "sucesso")
        return redirect(url_for("restaurante.cupons"))

    return render_template("restaurante/cupom_form.html", cupom=None, form={})


@restaurante_bp.route("/cupons/<int:id_cupom>/editar", methods=["GET", "POST"])
@login_requerido("restaurante")
def cupom_editar(id_cupom):
    cupom = models.buscar_cupom(id_cupom)
    if not cupom or cupom["id_restaurante"] != session["user_id"]:
        flash("Cupom não encontrado.", "erro")
        return redirect(url_for("restaurante.cupons"))

    if request.method == "POST":
        dados, erro = _validar_form_cupom(request.form)
        if erro:
            flash(erro, "erro")
            return render_template("restaurante/cupom_form.html", cupom=cupom, form=request.form)

        # Se trocou o código, checa se não colide com outro
        if dados["codigo"] != cupom["codigo"]:
            existente = models.buscar_cupom_por_codigo(dados["codigo"])
            if existente:
                flash(f"Já existe um cupom com o código '{dados['codigo']}'.", "erro")
                return render_template("restaurante/cupom_form.html", cupom=cupom, form=request.form)

        try:
            models.atualizar_cupom(
                id_cupom,
                codigo=dados["codigo"],
                descricao=dados["descricao"],
                tipo=dados["tipo"],
                valor=dados["valor"],
                valor_minimo_pedido=dados["valor_minimo_pedido"],
                valor_maximo_desconto=dados["valor_maximo_desconto"],
                data_inicio=dados["data_inicio"],
                data_fim=dados["data_fim"],
                limite_usos_total=dados["limite_usos_total"],
                limite_usos_por_cliente=dados["limite_usos_por_cliente"],
                ativo=dados["ativo"],
            )
        except Exception as e:
            flash(f"Erro ao atualizar cupom: {e}", "erro")
            return render_template("restaurante/cupom_form.html", cupom=cupom, form=request.form)

        flash(f"Cupom '{dados['codigo']}' atualizado.", "sucesso")
        return redirect(url_for("restaurante.cupons"))

    return render_template("restaurante/cupom_form.html", cupom=cupom, form={})


@restaurante_bp.route("/cupons/<int:id_cupom>/excluir", methods=["POST"])
@login_requerido("restaurante")
def cupom_excluir(id_cupom):
    cupom = models.buscar_cupom(id_cupom)
    if not cupom or cupom["id_restaurante"] != session["user_id"]:
        flash("Cupom não encontrado.", "erro")
        return redirect(url_for("restaurante.cupons"))

    if cupom["usos_atuais"] and cupom["usos_atuais"] > 0:
        flash(
            "Este cupom já foi usado em pedidos e não pode ser excluído. "
            "Você pode desativá-lo para impedir novos usos.",
            "erro",
        )
        return redirect(url_for("restaurante.cupons"))

    models.deletar_cupom(id_cupom)
    flash(f"Cupom '{cupom['codigo']}' removido.", "sucesso")
    return redirect(url_for("restaurante.cupons"))


@restaurante_bp.route("/cupons/<int:id_cupom>/alternar-ativo", methods=["POST"])
@login_requerido("restaurante")
def cupom_alternar_ativo(id_cupom):
    cupom = models.buscar_cupom(id_cupom)
    if not cupom or cupom["id_restaurante"] != session["user_id"]:
        flash("Cupom não encontrado.", "erro")
        return redirect(url_for("restaurante.cupons"))

    novo = not bool(cupom["ativo"])
    models.atualizar_cupom(id_cupom, ativo=novo)
    estado = "ativado" if novo else "desativado"
    flash(f"Cupom '{cupom['codigo']}' {estado}.", "sucesso")
    return redirect(url_for("restaurante.cupons"))


# ---------------------------------------------------------
# PERFIL (com foto)
# ---------------------------------------------------------
@restaurante_bp.route("/perfil", methods=["GET", "POST"])
@login_requerido("restaurante")
def editar_perfil():
    if request.method == "POST":
        foto_raw = request.form.get("foto_url")
        foto_url = _url_valida(foto_raw)
        if foto_url is False:
            flash("URL da foto inválida. Use http:// ou https://", "erro")
            return redirect(url_for("restaurante.editar_perfil"))

        models.atualizar_usuario(
            session["user_id"],
            request.form["nome_responsavel"],
            request.form.get("telefone"),
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
            foto_url=foto_url,
        )

        flash("Perfil do restaurante atualizado.", "sucesso")
        return redirect(url_for("restaurante.editar_perfil"))

    restaurante = models.buscar_restaurante(session["user_id"])
    return render_template("restaurante/editar_perfil.html", restaurante=restaurante)