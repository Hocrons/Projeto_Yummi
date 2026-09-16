import os
import time
import secrets
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import oauth
from models import models
from services import otp, verificacao_email, verificacao_whatsapp_local
from utils import normalizar_telefone, mascarar_email, mascarar_telefone

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

CATEGORIAS = [
    "Açaí", "Árabe", "Asiática", "Baiana", "Bebidas", "Brasileira",
    "Cafeteria", "Carnes", "Casa de Lanches", "Chinesa", "Comida de Boteco",
    "Congelados", "Confeitaria", "Coreana", "Crepe", "Doces & Bolos",
    "Express", "Farmácia", "Fast Food", "Fit / Saudável", "Frutos do Mar",
    "Gaúcha", "Hamburgueria", "Indiana", "Italiana", "Japonesa", "Marmita",
    "Mercado", "Mediterrânea", "Mexicana", "Mineira", "Nordestina", "Padaria",
    "Pastelaria", "Pet Shop", "Peixes", "Pizzaria", "Restaurantes",
    "Salgados", "Shopping", "Sobremesas", "Sorvetes", "Sopas & Caldos",
    "Tapiocaria", "Vegana", "Vegetariana", "Yakisoba",
]


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _fluxo_atual():
    return session.get("fluxo_entrada")


def _codigo_valido(fluxo):
    if not fluxo or "codigo_esperado" not in fluxo:
        return False
    idade = time.time() - fluxo.get("codigo_gerado_em", 0)
    return idade <= otp.CODIGO_VALIDADE_SEGUNDOS


def _fluxo_restaurante():
    return session.get("fluxo_restaurante")


def _codigo_restaurante_valido(fluxo, chave_codigo, chave_gerado_em):
    if not fluxo or chave_codigo not in fluxo:
        return False
    idade = time.time() - fluxo.get(chave_gerado_em, 0)
    return idade <= otp.CODIGO_VALIDADE_SEGUNDOS


def _codigo_entrega_padrao(telefone_normalizado):
    """Retorna os 4 últimos dígitos do telefone normalizado ou None."""
    digitos = "".join(c for c in (telefone_normalizado or "") if c.isdigit())
    return digitos[-4:] if len(digitos) >= 4 else None


def _nominatim_query(endereco):
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "format": "json",
                "limit": 1,
                "q": endereco,
                "countrycodes": "br",
                "addressdetails": 0,
            },
            headers={"User-Agent": "YummyApp/1.0 (projeto academico)"},
            timeout=6,
        )
        if resp.ok:
            dados = resp.json()
            if dados:
                return float(dados[0]["lat"]), float(dados[0]["lon"])
    except Exception as e:
        print(f"[Nominatim] Erro na consulta '{endereco}': {e}")
    return None, None


def _buscar_coordenadas(rua, numero, bairro, cidade, uf):
    tentativas = []

    if rua and numero and bairro and cidade and uf:
        tentativas.append((f"{rua}, {numero}, {bairro}, {cidade}, {uf}, Brasil", "rua"))
    if rua and numero and cidade and uf:
        tentativas.append((f"{rua}, {numero}, {cidade}, {uf}, Brasil", "rua"))
    if rua and cidade and uf:
        tentativas.append((f"{rua}, {cidade}, {uf}, Brasil", "rua"))
    if rua and cidade:
        tentativas.append((f"{rua}, {cidade}, Brasil", "rua"))
    if rua and bairro and cidade:
        tentativas.append((f"{rua}, {bairro}, {cidade}, Brasil", "rua"))

    if bairro and cidade and uf:
        tentativas.append((f"{bairro}, {cidade}, {uf}, Brasil", "bairro"))
    if bairro and cidade:
        tentativas.append((f"{bairro}, {cidade}, Brasil", "bairro"))
    if cidade and uf:
        tentativas.append((f"{cidade}, {uf}, Brasil", "cidade"))
    if cidade:
        tentativas.append((f"{cidade}, Brasil", "cidade"))

    vistas = set()
    unicas = []
    for t, p in tentativas:
        if t not in vistas:
            vistas.add(t)
            unicas.append((t, p))

    for i, (endereco, precisao) in enumerate(unicas):
        if i > 0:
            time.sleep(1.1)
        print(f"[Nominatim] Tentando ({precisao}): {endereco}")
        lat, lon = _nominatim_query(endereco)
        if lat is not None:
            print(f"[Nominatim] ✓ Encontrado ({precisao}): {lat}, {lon}")
            return lat, lon, endereco, precisao

    print("[Nominatim] ✗ Nenhuma tentativa funcionou.")
    return None, None, None, None


# =========================================================
# CLIENTE
# =========================================================
@auth_bp.route("/cliente/cadastrar", methods=["GET", "POST"])
def cadastrar_cliente():
    if request.method == "POST":
        try:
            if models.buscar_usuario_por_email(request.form["email"]):
                flash("Este e-mail já está cadastrado.", "erro")
                return render_template("cliente/cadastrar.html")

            telefone_raw = request.form.get("telefone")
            id_usuario = models.criar_usuario(
                nome=request.form["nome"],
                email=request.form["email"],
                senha=request.form["senha"],
                telefone=telefone_raw,
                tipo="cliente",
            )
            models.criar_cliente(
                id_usuario=id_usuario,
                cpf=request.form["cpf"],
                apelido=request.form.get("apelido"),
                codigo_entrega=_codigo_entrega_padrao(normalizar_telefone(telefone_raw)),
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
            session.permanent = True
            session["user_id"] = usuario["id"]
            session["user_tipo"] = "cliente"
            session["user_nome"] = usuario["nome"]
            session.setdefault("carrinho", {"id_restaurante": None, "itens": {}})
            return redirect(url_for("home.index"))
        flash("E-mail ou senha inválidos.", "erro")
    return render_template("cliente/login.html")


def _logar_usuario_cliente(usuario):
    session.permanent = True
    session["user_id"] = usuario["id"]
    session["user_tipo"] = "cliente"
    session["user_nome"] = usuario["nome"]
    session.setdefault("carrinho", {"id_restaurante": None, "itens": {}})


# ---------------------------------------------------------
# ENTRADA UNIFICADA (cliente)
# ---------------------------------------------------------
@auth_bp.route("/entrar")
def entrar():
    return render_template("cliente/entrar.html")


@auth_bp.route("/celular", methods=["GET", "POST"])
def entrada_celular():
    if request.method == "POST":
        telefone = normalizar_telefone(request.form.get("telefone", ""))
        if not telefone:
            flash("Informe um número de celular válido.", "erro")
            return render_template("cliente/celular.html")

        codigo = otp.gerar_codigo()
        sucesso, erro = verificacao_whatsapp_local.enviar_codigo(telefone, codigo)
        if not sucesso:
            flash(erro, "erro")
            return render_template("cliente/celular.html")

        session["fluxo_entrada"] = {
            "metodo": "celular",
            "telefone": telefone,
            "codigo_esperado": codigo,
            "codigo_gerado_em": time.time(),
        }
        flash(f"Enviamos um código por WhatsApp para {mascarar_telefone(telefone)}.", "sucesso")
        return redirect(url_for("auth.entrada_celular_codigo"))

    return render_template("cliente/celular.html")


@auth_bp.route("/celular/codigo", methods=["GET", "POST"])
def entrada_celular_codigo():
    fluxo = _fluxo_atual()
    if not fluxo or fluxo.get("metodo") != "celular":
        flash("Sessão expirada. Informe seu celular novamente.", "erro")
        return redirect(url_for("auth.entrada_celular"))

    if request.method == "POST":
        codigo_digitado = (request.form.get("codigo") or "").strip()

        if not _codigo_valido(fluxo):
            flash("O código expirou. Peça um novo código.", "erro")
        elif not codigo_digitado or codigo_digitado != fluxo.get("codigo_esperado"):
            flash("Código inválido. Confira e tente de novo.", "erro")
        else:
            usuario = models.buscar_usuario_por_telefone(fluxo["telefone"])

            if usuario and usuario["tipo"] != "cliente":
                flash(f"Esse celular já está associado a uma conta de {usuario['tipo']}.", "erro")
                session.pop("fluxo_entrada", None)
                return redirect(url_for("auth.entrar"))

            if usuario:
                fluxo["id_usuario_existente"] = usuario["id"]
                fluxo["email_cadastrado"] = usuario["email"]
                session["fluxo_entrada"] = fluxo
                return redirect(url_for("auth.entrada_celular_confirmar_email"))

            fluxo["telefone_verificado"] = True
            session["fluxo_entrada"] = fluxo
            return redirect(url_for("auth.cadastro_rapido"))

    return render_template("cliente/codigo.html", destino=mascarar_telefone(fluxo["telefone"]),
                            canal="WhatsApp", voltar_url=url_for("auth.entrada_celular"))


@auth_bp.route("/celular/confirmar-email", methods=["GET", "POST"])
def entrada_celular_confirmar_email():
    fluxo = _fluxo_atual()
    if not fluxo or "email_cadastrado" not in fluxo:
        flash("Sessão expirada. Informe seu celular novamente.", "erro")
        return redirect(url_for("auth.entrada_celular"))

    if request.method == "POST":
        email_digitado = (request.form.get("email") or "").strip().lower()
        if email_digitado == fluxo["email_cadastrado"].strip().lower():
            usuario = models.buscar_usuario_por_id(fluxo["id_usuario_existente"])
            _logar_usuario_cliente(usuario)
            session.pop("fluxo_entrada", None)
            flash("Login realizado com sucesso!", "sucesso")
            return redirect(url_for("home.index"))
        flash("O e-mail não corresponde ao cadastrado. Tente novamente.", "erro")

    return render_template("cliente/confirmar_email.html",
                            email_mascarado=mascarar_email(fluxo["email_cadastrado"]))


@auth_bp.route("/email", methods=["GET", "POST"])
def entrada_email():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if not email or "@" not in email:
            flash("Informe um e-mail válido.", "erro")
            return render_template("cliente/email.html")

        codigo = otp.gerar_codigo()
        sucesso, erro = verificacao_email.enviar_codigo(email, codigo)
        if not sucesso:
            flash(erro, "erro")
            return render_template("cliente/email.html")

        session["fluxo_entrada"] = {
            "metodo": "email",
            "email": email,
            "codigo_esperado": codigo,
            "codigo_gerado_em": time.time(),
        }
        flash(f"Enviamos um código para {email}.", "sucesso")
        return redirect(url_for("auth.entrada_email_codigo"))

    return render_template("cliente/email.html")


@auth_bp.route("/email/codigo", methods=["GET", "POST"])
def entrada_email_codigo():
    fluxo = _fluxo_atual()
    if not fluxo or fluxo.get("metodo") != "email":
        flash("Sessão expirada. Informe seu e-mail novamente.", "erro")
        return redirect(url_for("auth.entrada_email"))

    if request.method == "POST":
        codigo_digitado = (request.form.get("codigo") or "").strip()

        if not _codigo_valido(fluxo):
            flash("O código expirou. Peça um novo código.", "erro")
        elif not codigo_digitado or codigo_digitado != fluxo.get("codigo_esperado"):
            flash("Código inválido. Confira e tente de novo.", "erro")
        else:
            fluxo["email_verificado"] = True
            usuario = models.buscar_usuario_por_email(fluxo["email"])

            if usuario and usuario["tipo"] != "cliente":
                flash(f"Esse e-mail já está associado a uma conta de {usuario['tipo']}.", "erro")
                session.pop("fluxo_entrada", None)
                return redirect(url_for("auth.entrar"))

            if usuario and usuario.get("telefone"):
                fluxo["id_usuario_existente"] = usuario["id"]
                fluxo["telefone_cadastrado"] = usuario["telefone"]
                session["fluxo_entrada"] = fluxo
                return redirect(url_for("auth.entrada_email_confirmar_celular"))

            if usuario:
                _logar_usuario_cliente(usuario)
                session.pop("fluxo_entrada", None)
                flash("Login realizado com sucesso!", "sucesso")
                return redirect(url_for("home.index"))

            session["fluxo_entrada"] = fluxo
            return redirect(url_for("auth.cadastro_rapido"))

    return render_template("cliente/codigo.html", destino=fluxo["email"],
                            canal="e-mail", voltar_url=url_for("auth.entrada_email"))


@auth_bp.route("/email/confirmar-celular", methods=["GET", "POST"])
def entrada_email_confirmar_celular():
    fluxo = _fluxo_atual()
    if not fluxo or "telefone_cadastrado" not in fluxo:
        flash("Sessão expirada. Informe seu e-mail novamente.", "erro")
        return redirect(url_for("auth.entrada_email"))

    if request.method == "POST":
        codigo = otp.gerar_codigo()
        sucesso, erro = verificacao_whatsapp_local.enviar_codigo(fluxo["telefone_cadastrado"], codigo)
        if not sucesso:
            flash(erro, "erro")
            return render_template("cliente/confirmar_celular.html",
                                    telefone_mascarado=mascarar_telefone(fluxo["telefone_cadastrado"]))

        fluxo["codigo_esperado"] = codigo
        fluxo["codigo_gerado_em"] = time.time()
        session["fluxo_entrada"] = fluxo
        return redirect(url_for("auth.entrada_email_confirmar_celular_codigo"))

    return render_template("cliente/confirmar_celular.html",
                            telefone_mascarado=mascarar_telefone(fluxo["telefone_cadastrado"]))


@auth_bp.route("/email/confirmar-celular/codigo", methods=["GET", "POST"])
def entrada_email_confirmar_celular_codigo():
    fluxo = _fluxo_atual()
    if not fluxo or "telefone_cadastrado" not in fluxo or "codigo_esperado" not in fluxo:
        flash("Sessão expirada. Informe seu e-mail novamente.", "erro")
        return redirect(url_for("auth.entrada_email"))

    if request.method == "POST":
        codigo_digitado = (request.form.get("codigo") or "").strip()

        if not _codigo_valido(fluxo):
            flash("O código expirou. Peça um novo código.", "erro")
        elif not codigo_digitado or codigo_digitado != fluxo.get("codigo_esperado"):
            flash("Código inválido. Confira e tente de novo.", "erro")
        else:
            usuario = models.buscar_usuario_por_id(fluxo["id_usuario_existente"])
            _logar_usuario_cliente(usuario)
            session.pop("fluxo_entrada", None)
            flash("Login realizado com sucesso!", "sucesso")
            return redirect(url_for("home.index"))

    return render_template("cliente/codigo.html",
                            destino=mascarar_telefone(fluxo["telefone_cadastrado"]),
                            canal="WhatsApp",
                            voltar_url=url_for("auth.entrada_email_confirmar_celular"))


@auth_bp.route("/cadastro-rapido", methods=["GET", "POST"])
def cadastro_rapido():
    fluxo = _fluxo_atual()
    if not fluxo or fluxo.get("metodo") not in ("celular", "email"):
        flash("Sessão expirada. Comece novamente.", "erro")
        return redirect(url_for("auth.entrar"))

    veio_do_celular = fluxo["metodo"] == "celular"

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = request.form.get("cpf", "").strip()

        if not nome or not cpf:
            flash("Preencha nome e CPF para continuar.", "erro")
            return render_template("cliente/cadastro_rapido.html", fluxo=fluxo, veio_do_celular=veio_do_celular)

        fluxo["nome"] = nome
        fluxo["cpf"] = cpf

        if veio_do_celular:
            email = request.form.get("email", "").strip().lower()
            if not email or "@" not in email:
                flash("Informe um e-mail válido.", "erro")
                return render_template("cliente/cadastro_rapido.html", fluxo=fluxo, veio_do_celular=veio_do_celular)
            if models.buscar_usuario_por_email(email):
                flash("Este e-mail já está cadastrado em outra conta.", "erro")
                return render_template("cliente/cadastro_rapido.html", fluxo=fluxo, veio_do_celular=veio_do_celular)

            fluxo["email"] = email
            session["fluxo_entrada"] = fluxo
            return _finalizar_cadastro_rapido()

        else:
            telefone = normalizar_telefone(request.form.get("telefone", ""))
            if not telefone:
                flash("Informe um celular válido.", "erro")
                return render_template("cliente/cadastro_rapido.html", fluxo=fluxo, veio_do_celular=veio_do_celular)
            if models.buscar_usuario_por_telefone(telefone):
                flash("Este celular já está cadastrado em outra conta.", "erro")
                return render_template("cliente/cadastro_rapido.html", fluxo=fluxo, veio_do_celular=veio_do_celular)

            codigo = otp.gerar_codigo()
            sucesso, erro = verificacao_whatsapp_local.enviar_codigo(telefone, codigo)
            if not sucesso:
                flash(erro, "erro")
                return render_template("cliente/cadastro_rapido.html", fluxo=fluxo, veio_do_celular=veio_do_celular)

            fluxo["telefone"] = telefone
            fluxo["codigo_esperado"] = codigo
            fluxo["codigo_gerado_em"] = time.time()
            session["fluxo_entrada"] = fluxo
            return redirect(url_for("auth.cadastro_rapido_verificar_celular"))

    return render_template("cliente/cadastro_rapido.html", fluxo=fluxo, veio_do_celular=veio_do_celular)


@auth_bp.route("/cadastro-rapido/verificar-celular", methods=["GET", "POST"])
def cadastro_rapido_verificar_celular():
    fluxo = _fluxo_atual()
    if not fluxo or "telefone" not in fluxo or "nome" not in fluxo:
        flash("Sessão expirada. Comece novamente.", "erro")
        return redirect(url_for("auth.entrar"))

    if request.method == "POST":
        codigo_digitado = (request.form.get("codigo") or "").strip()

        if not _codigo_valido(fluxo):
            flash("O código expirou. Peça um novo código.", "erro")
        elif not codigo_digitado or codigo_digitado != fluxo.get("codigo_esperado"):
            flash("Código inválido. Confira e tente de novo.", "erro")
        else:
            fluxo["telefone_verificado"] = True
            session["fluxo_entrada"] = fluxo
            return _finalizar_cadastro_rapido()

    return render_template("cliente/codigo.html", destino=mascarar_telefone(fluxo["telefone"]),
                            canal="WhatsApp", voltar_url=url_for("auth.cadastro_rapido"))


def _finalizar_cadastro_rapido():
    fluxo = _fluxo_atual()
    try:
        senha_aleatoria = secrets.token_urlsafe(24)
        id_usuario = models.criar_usuario(
            nome=fluxo["nome"],
            email=fluxo["email"],
            senha=senha_aleatoria,
            telefone=fluxo["telefone"],
            tipo="cliente",
        )
        models.criar_cliente(
            id_usuario=id_usuario,
            cpf=fluxo["cpf"],
            apelido=None,
            codigo_entrega=_codigo_entrega_padrao(fluxo.get("telefone")),
        )
    except Exception as e:
        flash(f"Erro ao concluir o cadastro: {e}", "erro")
        return redirect(url_for("auth.cadastro_rapido"))

    session.pop("fluxo_entrada", None)
    usuario = {"id": id_usuario, "nome": fluxo["nome"]}
    _logar_usuario_cliente(usuario)
    flash("Cadastro concluído! Bem-vindo(a) ao Yummy.", "sucesso")
    return redirect(url_for("home.index"))


# ---------------------------------------------------------
# LOGIN SOCIAL
# ---------------------------------------------------------
def _login_ou_cadastrar_social(email, nome, provider):
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
            senha_aleatoria = secrets.token_urlsafe(24)
            telefone_raw = request.form.get("telefone")

            id_usuario = models.criar_usuario(
                nome=nome_final,
                email=dados["email"],
                senha=senha_aleatoria,
                telefone=telefone_raw,
                tipo="cliente",
            )
            models.criar_cliente(
                id_usuario=id_usuario,
                cpf=request.form["cpf"],
                apelido=request.form.get("apelido"),
                codigo_entrega=_codigo_entrega_padrao(normalizar_telefone(telefone_raw)),
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


# =========================================================
# RESTAURANTE — CADASTRO EM 6 ETAPAS
# =========================================================

@auth_bp.route("/restaurante/cadastrar", methods=["GET", "POST"])
def cadastrar_restaurante():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if not email or "@" not in email:
            flash("Informe um e-mail válido.", "erro")
            return render_template("restaurante/cadastrar_email.html")

        if models.buscar_usuario_por_email(email):
            flash("Este e-mail já está cadastrado.", "erro")
            return render_template("restaurante/cadastrar_email.html")

        codigo = otp.gerar_codigo()
        sucesso, erro = verificacao_email.enviar_codigo(email, codigo)
        if not sucesso:
            flash(erro, "erro")
            return render_template("restaurante/cadastrar_email.html")

        session["fluxo_restaurante"] = {
            "email": email,
            "codigo_email_esperado": codigo,
            "codigo_email_gerado_em": time.time(),
        }
        flash(f"Enviamos um código para {email}.", "sucesso")
        return redirect(url_for("auth.restaurante_email_codigo"))

    fluxo = _fluxo_restaurante()
    if fluxo:
        if fluxo.get("dados_salvos"):
            return redirect(url_for("auth.restaurante_confirmar_local"))
        if fluxo.get("telefone_verificado"):
            return redirect(url_for("auth.restaurante_completar"))
        if fluxo.get("email_verificado") and not fluxo.get("nome_responsavel"):
            return redirect(url_for("auth.restaurante_dados"))
        if fluxo.get("email_verificado"):
            return redirect(url_for("auth.restaurante_whatsapp_codigo"))

    return render_template("restaurante/cadastrar_email.html")


@auth_bp.route("/restaurante/cadastrar/email-codigo", methods=["GET", "POST"])
def restaurante_email_codigo():
    fluxo = _fluxo_restaurante()
    if not fluxo or "codigo_email_esperado" not in fluxo:
        flash("Sessão expirada. Informe seu e-mail novamente.", "erro")
        return redirect(url_for("auth.cadastrar_restaurante"))

    if request.method == "POST":
        codigo_digitado = (request.form.get("codigo") or "").strip()

        if not _codigo_restaurante_valido(fluxo, "codigo_email_esperado", "codigo_email_gerado_em"):
            flash("O código expirou. Peça um novo código.", "erro")
        elif not codigo_digitado or codigo_digitado != fluxo.get("codigo_email_esperado"):
            flash("Código inválido. Confira e tente de novo.", "erro")
        else:
            fluxo["email_verificado"] = True
            session["fluxo_restaurante"] = fluxo
            return redirect(url_for("auth.restaurante_dados"))

    return render_template("restaurante/cadastrar_email_codigo.html",
                           email=fluxo["email"],
                           voltar_url=url_for("auth.cadastrar_restaurante"))


@auth_bp.route("/restaurante/cadastrar/dados", methods=["GET", "POST"])
def restaurante_dados():
    fluxo = _fluxo_restaurante()
    if not fluxo or not fluxo.get("email_verificado"):
        flash("Confirme seu e-mail primeiro.", "erro")
        return redirect(url_for("auth.cadastrar_restaurante"))

    if request.method == "POST":
        nome = (request.form.get("nome_responsavel") or "").strip()
        telefone_raw = request.form.get("telefone") or ""

        if not nome:
            flash("Informe o nome do responsável.", "erro")
            return render_template("restaurante/cadastrar_dados.html", fluxo=fluxo)

        telefone = normalizar_telefone(telefone_raw)
        if not telefone:
            flash("Informe um celular válido com DDD.", "erro")
            return render_template("restaurante/cadastrar_dados.html", fluxo=fluxo)

        if models.buscar_usuario_por_telefone(telefone):
            flash("Este celular já está cadastrado em outra conta.", "erro")
            return render_template("restaurante/cadastrar_dados.html", fluxo=fluxo)

        codigo = otp.gerar_codigo()
        sucesso, erro = verificacao_whatsapp_local.enviar_codigo(telefone, codigo)
        if not sucesso:
            flash(erro, "erro")
            return render_template("restaurante/cadastrar_dados.html", fluxo=fluxo)

        fluxo["nome_responsavel"] = nome
        fluxo["telefone"] = telefone
        fluxo["codigo_wpp_esperado"] = codigo
        fluxo["codigo_wpp_gerado_em"] = time.time()
        session["fluxo_restaurante"] = fluxo
        flash(f"Enviamos um código por WhatsApp para {mascarar_telefone(telefone)}.", "sucesso")
        return redirect(url_for("auth.restaurante_whatsapp_codigo"))

    return render_template("restaurante/cadastrar_dados.html", fluxo=fluxo)


@auth_bp.route("/restaurante/cadastrar/whatsapp-codigo", methods=["GET", "POST"])
def restaurante_whatsapp_codigo():
    fluxo = _fluxo_restaurante()
    if not fluxo or "codigo_wpp_esperado" not in fluxo:
        flash("Sessão expirada. Comece novamente.", "erro")
        return redirect(url_for("auth.cadastrar_restaurante"))

    if request.method == "POST":
        codigo_digitado = (request.form.get("codigo") or "").strip()

        if not _codigo_restaurante_valido(fluxo, "codigo_wpp_esperado", "codigo_wpp_gerado_em"):
            flash("O código expirou. Peça um novo código.", "erro")
        elif not codigo_digitado or codigo_digitado != fluxo.get("codigo_wpp_esperado"):
            flash("Código inválido. Confira e tente de novo.", "erro")
        else:
            fluxo["telefone_verificado"] = True
            session["fluxo_restaurante"] = fluxo
            return redirect(url_for("auth.restaurante_completar"))

    return render_template("restaurante/cadastrar_wpp_codigo.html",
                           telefone_mascarado=mascarar_telefone(fluxo["telefone"]),
                           voltar_url=url_for("auth.restaurante_dados"))


@auth_bp.route("/restaurante/cadastrar/completar", methods=["GET", "POST"])
def restaurante_completar():
    fluxo = _fluxo_restaurante()
    if not fluxo or not fluxo.get("telefone_verificado"):
        flash("Confirme seu celular primeiro.", "erro")
        return redirect(url_for("auth.cadastrar_restaurante"))

    if request.method == "POST":
        id_plano = request.form.get("id_plano") or None
        if not id_plano:
            flash("Escolha um plano para continuar.", "erro")
            return render_template("restaurante/cadastrar.html",
                                   fluxo=fluxo,
                                   form_dados=request.form,
                                   categorias=CATEGORIAS,
                                   planos=models.listar_planos())

        rua = request.form.get("rua") or ""
        numero = request.form.get("numero") or ""
        bairro = request.form.get("bairro") or ""
        cidade = request.form.get("cidade") or ""
        uf = request.form.get("estado") or ""
        cep = request.form.get("cep") or ""

        lat, lon, endereco_usado, precisao = _buscar_coordenadas(rua, numero, bairro, cidade, uf)

        fluxo["form_dados"] = {
            "senha": request.form.get("senha"),
            "nome_fantasia": request.form.get("nome_fantasia"),
            "cnpj": request.form.get("cnpj"),
            "categoria": request.form.get("categoria"),
            "tem_mesa": request.form.get("tem_mesa"),
            "taxa_entrega": request.form.get("taxa_entrega") or "0",
            "horario_funcionamento": request.form.get("horario_funcionamento"),
            "rua": rua,
            "numero": numero,
            "bairro": bairro,
            "cidade": cidade,
            "estado": uf,
            "cep": cep,
            "complemento": request.form.get("complemento"),
            "cpf_representante": request.form.get("cpf_representante"),
            "nome_representante": request.form.get("nome_representante"),
            "data_nasc_representante": request.form.get("data_nasc_representante"),
            "id_plano": id_plano,
            "lat": lat,
            "lon": lon,
            "endereco_usado": endereco_usado,
            "precisao": precisao,
        }
        fluxo["dados_salvos"] = True
        session["fluxo_restaurante"] = fluxo
        return redirect(url_for("auth.restaurante_confirmar_local"))

    return render_template("restaurante/cadastrar.html",
                           fluxo=fluxo,
                           form_dados=fluxo.get("form_dados", {}),
                           categorias=CATEGORIAS,
                           planos=models.listar_planos())


@auth_bp.route("/restaurante/cadastrar/confirmar-local", methods=["GET", "POST"])
def restaurante_confirmar_local():
    fluxo = _fluxo_restaurante()
    if not fluxo or not fluxo.get("dados_salvos"):
        flash("Sessão expirada. Comece novamente.", "erro")
        return redirect(url_for("auth.cadastrar_restaurante"))

    form = fluxo.get("form_dados", {})

    if request.method == "POST":
        try:
            tem_mesa = 1 if form.get("tem_mesa") == "1" else 0
            id_usuario = models.criar_usuario(
                nome=fluxo["nome_responsavel"],
                email=fluxo["email"],
                senha=form["senha"],
                telefone=fluxo["telefone"],
                tipo="restaurante",
            )
            models.criar_restaurante(
                id_usuario=id_usuario,
                nome_fantasia=form["nome_fantasia"],
                cnpj=form["cnpj"],
                categoria=form.get("categoria"),
                taxa_entrega=form.get("taxa_entrega") or 0,
                horario_funcionamento=form.get("horario_funcionamento"),
                rua=form.get("rua"),
                numero=form.get("numero"),
                bairro=form.get("bairro"),
                cidade=form.get("cidade"),
                cep=form.get("cep"),
                tem_mesa=tem_mesa,
                complemento=form.get("complemento"),
                cpf_representante=form.get("cpf_representante"),
                nome_representante=form.get("nome_representante"),
                data_nasc_representante=form.get("data_nasc_representante"),
                id_plano=form.get("id_plano"),
            )
        except Exception as e:
            flash(f"Erro ao cadastrar: {e}", "erro")
            return redirect(url_for("auth.restaurante_confirmar_local"))

        session.pop("fluxo_restaurante", None)
        flash("Restaurante cadastrado! Faça login para continuar.", "sucesso")
        return redirect(url_for("auth.login_restaurante"))

    endereco_completo = ", ".join(filter(None, [
        form.get("rua"),
        form.get("numero"),
        form.get("bairro"),
        form.get("cidade"),
        form.get("estado"),
        form.get("cep"),
    ]))

    return render_template("restaurante/cadastrar_confirmar_local.html",
                           form=form,
                           endereco_completo=endereco_completo,
                           lat=form.get("lat"),
                           lon=form.get("lon"),
                           precisao=form.get("precisao"),
                           voltar_url=url_for("auth.restaurante_completar"))


@auth_bp.route("/restaurante/login", methods=["GET", "POST"])
def login_restaurante():
    if request.method == "POST":
        usuario = models.validar_login(request.form["email"], request.form["senha"])
        if usuario and usuario["tipo"] == "restaurante":
            session.permanent = True
            session["user_id"] = usuario["id"]
            session["user_tipo"] = "restaurante"
            session["user_nome"] = usuario["nome"]
            return redirect(url_for("restaurante.painel"))
        flash("E-mail ou senha inválidos.", "erro")
    return render_template("restaurante/login.html")


# =========================================================
# ENTREGADOR
# =========================================================
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
            session.permanent = True
            session["user_id"] = usuario["id"]
            session["user_tipo"] = "entregador"
            session["user_nome"] = usuario["nome"]
            return redirect(url_for("entregador.painel"))
        flash("E-mail ou senha inválidos.", "erro")
    return render_template("entregador/login.html")


# =========================================================
# LOGOUT
# =========================================================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing.index"))