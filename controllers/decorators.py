from functools import wraps
from flask import session, redirect, url_for, flash


_LOGIN_ENDPOINT = {
    "cliente": "auth.login_cliente",
    "restaurante": "auth.login_restaurante",
    "entregador": "auth.login_entregador",
}

_NOME_TIPO = {
    "cliente": "cliente",
    "restaurante": "restaurante",
    "entregador": "entregador",
}


def login_requerido(tipo):
    """
    Exige que exista uma sessão ativa do 'tipo' informado
    ('cliente', 'restaurante' ou 'entregador').
    """
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            tipo_atual = session.get("user_tipo")

            if tipo_atual == tipo:
                return f(*args, **kwargs)

            destino = _LOGIN_ENDPOINT.get(tipo, "auth.entrar")

            if tipo_atual and tipo_atual != tipo:
                flash(
                    f"Você está logado como {_NOME_TIPO.get(tipo_atual, tipo_atual)}. "
                    f"Saia da conta atual para entrar como {_NOME_TIPO.get(tipo, tipo)}.",
                    "erro",
                )
            else:
                flash("Você precisa entrar na sua conta para continuar.", "erro")

            return redirect(url_for(destino))
        return wrapper
    return decorador