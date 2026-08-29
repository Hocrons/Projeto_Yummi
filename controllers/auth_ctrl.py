import os
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import oauth
from models import models

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# URL base fixa para o redirect_uri do OAuth. Usar uma URL fixa (em vez de
# url_for(..., _external=True)) evita o erro "redirect_uri_mismatch": o
# Flask não fica dependente do Host que o navegador mandou (localhost vs
# 127.0.0.1 são domínios DIFERENTES para o Google/Facebook).
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

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
            session.setdefault("carrinho", {"id_restaurante": None, "itens": {}})
            return redirect(url_for("home.index"))
        flash("E-mail ou senha inválidos.", "erro")
    return render_template("cliente/login.html")


# ---------------------------------------------------------
# LOGIN SOCIAL (Google / Facebook) - apenas para clientes
# ---------------------------------------------------------
def _logar_usuario_cliente(usuario):
    session["user_id"] = usuario["id"]
    session["user_tipo"] = "cliente"
    session["user_nome"] = usuario["nome"]
    session.setdefault("carrinho", {"id_restaurante": None, "itens": {}})


def _login_ou_cadastrar_social(email, nome, provider):
    """
    Se já existe uma conta de CLIENTE com esse e-mail, loga direto.
    Se o e-mail já pertence a um restaurante/entregador, bloqueia (contas
    são por tipo de usuário e não podem se misturar).
    Se não existe ninguém com esse e-mail, manda para uma tela rápida
    pedindo o CPF (obrigatório no nosso modelo de dados) antes de criar
    a conta de cliente.
    """
    usuario = models.buscar_usuario_por_email(email)

    if usuario:
        if usuario["tipo"] != "cliente":
            flash(
                f"Este e-mail já está cadastrado como conta de {usuario['tipo']}. "
                f"Use a tela de login de {usuario['tipo']} ou outro e-mail.",
                "erro",
            )
            return redirect(url_for("auth.login_cliente"))

        _logar_usuario_cliente(usuario)
        flash(f"Login com {provider.capitalize()} realizado!", "sucesso")
        return redirect(url_for("home.index"))

    # Ainda não existe conta -> guarda os dados do provedor na sessão
    # e pede só o CPF/telefone para concluir o cadastro.
    session["cadastro_social"] = {"email": email, "nome": nome, "provider": provider}
    return redirect(url_for("auth.completar_cadastro_social"))


@auth_bp.route("/google/login")
def login_google():
    redirect_uri = f"{BASE_URL}{url_for('auth.callback_google')}"
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def callback_google():
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or {}
        email = userinfo.get("email")
        nome = userinfo.get("name", "")
    except Exception:
        flash("Não foi possível concluir o login com Google. Tente novamente.", "erro")
        return redirect(url_for("auth.login_cliente"))

    if not email:
        flash("Não foi possível obter seu e-mail do Google.", "erro")
        return redirect(url_for("auth.login_cliente"))

    return _login_ou_cadastrar_social(email, nome, "google")


@auth_bp.route("/facebook/login")
def login_facebook():
    redirect_uri = f"{BASE_URL}{url_for('auth.callback_facebook')}"
    return oauth.facebook.authorize_redirect(redirect_uri)


@auth_bp.route("/facebook/callback")
def callback_facebook():
    try:
        token = oauth.facebook.authorize_access_token()
        resp = oauth.facebook.get("me?fields=id,name,email", token=token)
        perfil = resp.json()
        email = perfil.get("email")
        nome = perfil.get("name", "")
    except Exception:
        flash("Não foi possível concluir o login com Facebook. Tente novamente.", "erro")
        return redirect(url_for("auth.login_cliente"))

    if not email:
        flash(
            "Seu Facebook não compartilhou um e-mail. "
            "Cadastre-se pelo formulário normal ou use outro método de login.",
            "erro",
        )
        return redirect(url_for("auth.login_cliente"))

    return _login_ou_cadastrar_social(email, nome, "facebook")


@auth_bp.route("/completar-cadastro", methods=["GET", "POST"])
def completar_cadastro_social():
    dados = session.get("cadastro_social")
    if not dados:
        flash("Sessão expirada. Tente entrar com Google/Facebook novamente.", "erro")
        return redirect(url_for("auth.login_cliente"))

    if request.method == "POST":
        nome_final = request.form.get("nome") or dados["nome"] or "Cliente"
        try:
            # Conta social não usa senha própria: gera uma senha aleatória
            # só para preencher o campo obrigatório da tabela usuario.
            senha_aleatoria = secrets.token_urlsafe(24)

            id_usuario = models.criar_usuario(
                nome=nome_final,
                email=dados["email"],
                senha=senha_aleatoria,
                telefone=request.form.get("telefone"),
                tipo="cliente",
            )
            models.criar_cliente(
                id_usuario=id_usuario,
                cpf=request.form["cpf"],
                apelido=request.form.get("apelido"),
            )
        except Exception as e:
            flash(f"Erro ao concluir o cadastro: {e}", "erro")
            return render_template("cliente/completar_cadastro_social.html", dados=dados)

        session.pop("cadastro_social", None)
        usuario = {"id": id_usuario, "nome": nome_final}
        _logar_usuario_cliente(usuario)
        flash("Cadastro concluído! Bem-vindo(a) ao Yummy.", "sucesso")
        return redirect(url_for("home.index"))

    return render_template("cliente/completar_cadastro_social.html", dados=dados)


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