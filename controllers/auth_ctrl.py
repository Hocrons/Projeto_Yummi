from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import models

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------------------------------------
# CLIENTE
# ---------------------------------------------------------
@auth_bp.route("/cliente/cadastrar", methods=["GET", "POST"])
def cadastrar_cliente():
    if request.method == "POST":
        try:
            if models.buscar_usuario_por_email(request.form["email"]):
                flash("Este e-mail já está cadastrado.", "erro")
                return render_template("cliente/cadastrar.html")

            id_usuario = models.criar_usuario(
                nome=request.form["nome"],
                email=request.form["email"],
                senha=request.form["senha"],
                telefone=request.form.get("telefone"),
                tipo="cliente",
            )
            models.criar_cliente(
                id_usuario=id_usuario,
                cpf=request.form["cpf"],
                apelido=request.form.get("apelido"),
            )
            flash("Cadastro realizado! Faça login para continuar.", "sucesso")
            return redirect(url_for("auth.login_cliente"))
        except Exception as e:
            flash(f"Erro ao cadastrar: {e}", "erro")
    return render_template("cliente/cadastrar.html")


@auth_bp.route("/cliente/login", methods=["GET", "POST"])
def login_cliente():
    if request.method == "POST":
        usuario = models.validar_login(request.form["email"], request.form["senha"])
        if usuario and usuario["tipo"] == "cliente":
            session["user_id"] = usuario["id"]
            session["user_tipo"] = "cliente"
            session["user_nome"] = usuario["nome"]
            session.setdefault("carrinho", {})
            return redirect(url_for("home.index"))
        flash("E-mail ou senha inválidos.", "erro")
    return render_template("cliente/login.html")


# ---------------------------------------------------------
# RESTAURANTE
# ---------------------------------------------------------
@auth_bp.route("/restaurante/cadastrar", methods=["GET", "POST"])
def cadastrar_restaurante():
    if request.method == "POST":
        try:
            if models.buscar_usuario_por_email(request.form["email"]):
                flash("Este e-mail já está cadastrado.", "erro")
                return render_template("restaurante/cadastrar.html")

            id_usuario = models.criar_usuario(
                nome=request.form["nome_responsavel"],
                email=request.form["email"],
                senha=request.form["senha"],
                telefone=request.form.get("telefone"),
                tipo="restaurante",
            )
            models.criar_restaurante(
                id_usuario=id_usuario,
                nome_fantasia=request.form["nome_fantasia"],
                cnpj=request.form["cnpj"],
                categoria=request.form.get("categoria"),
                taxa_entrega=request.form.get("taxa_entrega") or 0,
                horario_funcionamento=request.form.get("horario_funcionamento"),
                rua=request.form.get("rua"),
                numero=request.form.get("numero"),
                bairro=request.form.get("bairro"),
                cidade=request.form.get("cidade"),
                cep=request.form.get("cep"),
            )
            flash("Restaurante cadastrado! Faça login para continuar.", "sucesso")
            return redirect(url_for("auth.login_restaurante"))
        except Exception as e:
            flash(f"Erro ao cadastrar: {e}", "erro")
    return render_template("restaurante/cadastrar.html")


@auth_bp.route("/restaurante/login", methods=["GET", "POST"])
def login_restaurante():
    if request.method == "POST":
        usuario = models.validar_login(request.form["email"], request.form["senha"])
        if usuario and usuario["tipo"] == "restaurante":
            session["user_id"] = usuario["id"]
            session["user_tipo"] = "restaurante"
            session["user_nome"] = usuario["nome"]
            return redirect(url_for("restaurante.painel"))
        flash("E-mail ou senha inválidos.", "erro")
    return render_template("restaurante/login.html")


# ---------------------------------------------------------
# ENTREGADOR
# ---------------------------------------------------------
@auth_bp.route("/entregador/cadastrar", methods=["GET", "POST"])
def cadastrar_entregador():
    if request.method == "POST":
        try:
            if models.buscar_usuario_por_email(request.form["email"]):
                flash("Este e-mail já está cadastrado.", "erro")
                return render_template("entregador/cadastrar.html")

            id_usuario = models.criar_usuario(
                nome=request.form["nome"],
                email=request.form["email"],
                senha=request.form["senha"],
                telefone=request.form.get("telefone"),
                tipo="entregador",
            )
            models.criar_entregador(
                id_usuario=id_usuario,
                cpf=request.form["cpf"],
                veiculo=request.form.get("veiculo"),
                placa=request.form.get("placa"),
            )
            flash("Cadastro realizado! Faça login para continuar.", "sucesso")
            return redirect(url_for("auth.login_entregador"))
        except Exception as e:
            flash(f"Erro ao cadastrar: {e}", "erro")
    return render_template("entregador/cadastrar.html")


@auth_bp.route("/entregador/login", methods=["GET", "POST"])
def login_entregador():
    if request.method == "POST":
        usuario = models.validar_login(request.form["email"], request.form["senha"])
        if usuario and usuario["tipo"] == "entregador":
            session["user_id"] = usuario["id"]
            session["user_tipo"] = "entregador"
            session["user_nome"] = usuario["nome"]
            return redirect(url_for("entregador.painel"))
        flash("E-mail ou senha inválidos.", "erro")
    return render_template("entregador/login.html")


# ---------------------------------------------------------
# LOGOUT (comum aos 3 tipos)
# ---------------------------------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.index"))
