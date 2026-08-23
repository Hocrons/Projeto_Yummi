"""Regras de negocio do cadastro de usuario.

O Controller nao conhece SQL e o Model nao conhece HTTP - as decisoes de
negocio (validar, normalizar, cifrar, checar unicidade) moram todas aqui.
"""
import bcrypt
from sqlalchemy import func, select

from app.extensions import db
from app.models.usuario import STATUS_CONTA, TIPOS_USUARIO, Usuario
from app.utils.errors import ErroDeConflito, ErroDeValidacao, NaoEncontrado
from app.utils.validators import (
    parse_data,
    so_digitos,
    validar_celular,
    validar_cpf,
    validar_data_nascimento,
    validar_email,
)

SENHA_TAMANHO_MINIMO = 8
# bcrypt trunca (e, na versao 5, rejeita) segredos acima de 72 bytes.
SENHA_TAMANHO_MAXIMO_BYTES = 72

# Campos que o proprio usuario pode alterar. cpf fica de fora: e a chave de
# negocio da pessoa e nao muda na vida real. tipo_usuario e status_conta sao
# administrativos e tem operacao propria (alterar_status).
CAMPOS_ATUALIZAVEIS = ("nome_completo", "email", "celular", "rg", "data_nascimento", "senha")


# ---------------------------------------------------------------- helpers

def _hash_senha(senha):
    if not isinstance(senha, str) or len(senha) < SENHA_TAMANHO_MINIMO:
        raise ErroDeValidacao(
            "senha", f"A senha deve ter ao menos {SENHA_TAMANHO_MINIMO} caracteres."
        )
    if len(senha.encode("utf-8")) > SENHA_TAMANHO_MAXIMO_BYTES:
        raise ErroDeValidacao(
            "senha", f"A senha deve ter no maximo {SENHA_TAMANHO_MAXIMO_BYTES} bytes."
        )
    # RNF04/RF09: nunca guardamos a senha em texto puro.
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def conferir_senha(senha, senha_hash):
    """Compara a senha informada com o hash guardado. Usado no login."""
    if not senha or not senha_hash:
        return False
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def _normalizar_contato(dados):
    """E-mail em minusculas e telefone/CPF so com digitos, antes de comparar."""
    email = (dados.get("email") or "").strip().lower() or None
    celular = so_digitos(dados.get("celular")) or None
    cpf = so_digitos(dados.get("cpf")) or None
    return email, celular, cpf


def _garantir_unicidade(email, celular, cpf, ignorar_id=None):
    """RF08: bloqueia e-mail, celular ou CPF ja existentes na base.

    `ignorar_id` exclui o proprio registro da checagem durante um update.
    """
    for campo, valor in (("email", email), ("celular", celular), ("cpf", cpf)):
        if not valor:
            continue
        consulta = select(Usuario).where(getattr(Usuario, campo) == valor)
        if ignorar_id is not None:
            consulta = consulta.where(Usuario.id_usuario != ignorar_id)
        if db.session.scalar(consulta) is not None:
            raise ErroDeConflito(campo, f"Ja existe um usuario cadastrado com este {campo}.")


# ---------------------------------------------------------------- CREATE

def criar_usuario(dados):
    """Cria a conta com status 'pendente' ate a validacao do codigo OTP (RF01/RF11)."""
    if not isinstance(dados, dict):
        raise ErroDeValidacao("corpo", "O corpo da requisicao deve ser um objeto JSON.")

    nome = (dados.get("nome_completo") or "").strip()
    if not 3 <= len(nome) <= 100:
        raise ErroDeValidacao("nome_completo", "O nome deve ter entre 3 e 100 caracteres.")

    email, celular, cpf = _normalizar_contato(dados)

    # RF02/RF03: o cadastro precisa de pelo menos uma forma de contato.
    if not email and not celular:
        raise ErroDeValidacao("contato", "Informe ao menos um e-mail ou um celular.")
    if email and not validar_email(email):
        raise ErroDeValidacao("email", "E-mail invalido.")
    if celular and not validar_celular(celular):
        raise ErroDeValidacao("celular", "Celular invalido. Use DDD + 9 digitos.")

    if not validar_cpf(cpf):
        raise ErroDeValidacao("cpf", "CPF invalido.")

    data_nascimento = parse_data(dados.get("data_nascimento"))
    if data_nascimento is None:
        raise ErroDeValidacao("data_nascimento", "Use o formato AAAA-MM-DD.")
    if not validar_data_nascimento(data_nascimento):
        raise ErroDeValidacao("data_nascimento", "O usuario deve ter ao menos 18 anos.")

    tipo_usuario = dados.get("tipo_usuario") or "cliente"
    if tipo_usuario not in TIPOS_USUARIO:
        raise ErroDeValidacao("tipo_usuario", f"Valores aceitos: {', '.join(TIPOS_USUARIO)}.")

    provedor_social = dados.get("provedor_social")
    senha = dados.get("senha")
    # Cadastro por Google/Facebook nao tem senha (RF05); o tradicional exige.
    if provedor_social:
        senha_hash = None
    else:
        if not senha:
            raise ErroDeValidacao("senha", "Campo obrigatorio no cadastro tradicional.")
        senha_hash = _hash_senha(senha)

    _garantir_unicidade(email, celular, cpf)

    usuario = Usuario(
        nome_completo=nome,
        email=email,
        celular=celular,
        cpf=cpf,
        rg=(dados.get("rg") or "").strip() or None,
        data_nascimento=data_nascimento,
        senha_hash=senha_hash,
        tipo_usuario=tipo_usuario,
        status_conta="pendente",
        provedor_social=provedor_social,
        id_social=dados.get("id_social"),
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


# ------------------------------------------------------------------ READ

def buscar_usuario(id_usuario):
    """Busca por id. Nao devolve contas ja excluidas."""
    usuario = db.session.get(Usuario, id_usuario)
    if usuario is None or usuario.status_conta == "excluido":
        raise NaoEncontrado(f"Usuario {id_usuario} nao encontrado.")
    return usuario


def listar_usuarios(pagina=1, por_pagina=20, tipo_usuario=None, busca=None):
    """Lista paginada, com filtro opcional por papel e por nome/e-mail."""
    pagina = max(1, int(pagina or 1))
    por_pagina = min(100, max(1, int(por_pagina or 20)))

    consulta = select(Usuario).where(Usuario.status_conta != "excluido")

    if tipo_usuario:
        if tipo_usuario not in TIPOS_USUARIO:
            raise ErroDeValidacao("tipo_usuario", f"Valores aceitos: {', '.join(TIPOS_USUARIO)}.")
        consulta = consulta.where(Usuario.tipo_usuario == tipo_usuario)

    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(
            Usuario.nome_completo.ilike(termo) | Usuario.email.ilike(termo)
        )

    total = db.session.scalar(select(func.count()).select_from(consulta.subquery()))
    itens = db.session.scalars(
        consulta.order_by(Usuario.id_usuario)
        .limit(por_pagina)
        .offset((pagina - 1) * por_pagina)
    ).all()

    return itens, total, pagina, por_pagina


# ---------------------------------------------------------------- UPDATE

def atualizar_usuario(id_usuario, dados):
    """Atualizacao parcial: so mexe nos campos presentes no corpo."""
    if not isinstance(dados, dict) or not dados:
        raise ErroDeValidacao("corpo", "Informe ao menos um campo para atualizar.")

    desconhecidos = set(dados) - set(CAMPOS_ATUALIZAVEIS)
    if desconhecidos:
        raise ErroDeValidacao(
            "corpo",
            f"Campos nao atualizaveis por esta rota: {', '.join(sorted(desconhecidos))}.",
        )

    usuario = buscar_usuario(id_usuario)

    if "nome_completo" in dados:
        nome = (dados.get("nome_completo") or "").strip()
        if not 3 <= len(nome) <= 100:
            raise ErroDeValidacao("nome_completo", "O nome deve ter entre 3 e 100 caracteres.")
        usuario.nome_completo = nome

    if "data_nascimento" in dados:
        data_nascimento = parse_data(dados.get("data_nascimento"))
        if data_nascimento is None:
            raise ErroDeValidacao("data_nascimento", "Use o formato AAAA-MM-DD.")
        if not validar_data_nascimento(data_nascimento):
            raise ErroDeValidacao("data_nascimento", "O usuario deve ter ao menos 18 anos.")
        usuario.data_nascimento = data_nascimento

    if "rg" in dados:
        usuario.rg = (dados.get("rg") or "").strip() or None

    # E-mail e celular sao avaliados juntos: o registro nao pode ficar sem contato.
    novo_email = usuario.email
    novo_celular = usuario.celular

    if "email" in dados:
        novo_email = (dados.get("email") or "").strip().lower() or None
        if novo_email and not validar_email(novo_email):
            raise ErroDeValidacao("email", "E-mail invalido.")

    if "celular" in dados:
        novo_celular = so_digitos(dados.get("celular")) or None
        if novo_celular and not validar_celular(novo_celular):
            raise ErroDeValidacao("celular", "Celular invalido. Use DDD + 9 digitos.")

    if not novo_email and not novo_celular:
        raise ErroDeValidacao("contato", "O usuario deve manter ao menos um e-mail ou celular.")

    _garantir_unicidade(
        novo_email if "email" in dados else None,
        novo_celular if "celular" in dados else None,
        None,
        ignorar_id=id_usuario,
    )
    usuario.email = novo_email
    usuario.celular = novo_celular

    if "senha" in dados:
        usuario.senha_hash = _hash_senha(dados.get("senha"))

    db.session.commit()
    return usuario


def alterar_status(id_usuario, novo_status):
    """Operacao administrativa: ativar apos o OTP, bloquear por abuso (RF10/RF11)."""
    if novo_status not in STATUS_CONTA:
        raise ErroDeValidacao("status_conta", f"Valores aceitos: {', '.join(STATUS_CONTA)}.")
    usuario = buscar_usuario(id_usuario)
    usuario.status_conta = novo_status
    db.session.commit()
    return usuario


# ---------------------------------------------------------------- DELETE

def excluir_usuario(id_usuario):
    """Exclusao logica.

    PEDIDO.id_usuario e FK NOT NULL: apagar a linha de verdade seria bloqueado
    pela integridade referencial assim que o usuario tivesse um pedido. Mesmo
    raciocinio que o projeto ja aplica em PRODUTO (`disponivel = false`).
    """
    usuario = buscar_usuario(id_usuario)
    usuario.status_conta = "excluido"
    db.session.commit()
    return usuario
