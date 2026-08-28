from functools import wraps
from flask import session, redirect, url_for, flash


def login_requerido(tipo):
    """
    Exige que exista uma sessão ativa do 'tipo' informado
    ('cliente', 'restaurante' ou 'entregador').
    """
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("user_tipo") != tipo:
                flash("Você precisa entrar na sua conta para continuar.", "erro")
                return redirect(url_for(f"auth.login_{tipo}"))
            return f(*args, **kwargs)
        return wrapper
    return decorador
