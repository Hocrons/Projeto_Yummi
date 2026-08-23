"""Validacoes de dominio do cadastro de usuario (RF02, RF03, RF07)."""
import re
from datetime import date

IDADE_MINIMA = 18

# Formato pratico de e-mail. A validacao definitiva e o envio do codigo OTP.
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def so_digitos(valor):
    """Remove tudo que nao for digito. Aceita None."""
    return re.sub(r"\D", "", valor or "")


def validar_cpf(cpf):
    """Valida os dois digitos verificadores pelo algoritmo modulo 11 (RF07).

    Rejeita sequencias com todos os digitos iguais (00000000000, 11111111111,
    ...), que passam na conta mas nao sao CPFs validos.
    """
    cpf = so_digitos(cpf)

    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False

    # Primeiro digito usa pesos 10..2; o segundo usa 11..2 e ja inclui o primeiro.
    for posicao in (9, 10):
        soma = sum(int(cpf[i]) * ((posicao + 1) - i) for i in range(posicao))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[posicao]):
            return False

    return True


def validar_email(email):
    """Valida o formato do e-mail e o limite de 254 caracteres do padrao SMTP."""
    if not email:
        return False
    return len(email) <= 254 and bool(_RE_EMAIL.match(email))


def validar_celular(celular):
    """Valida celular brasileiro: 11 digitos, DDD valido e nono digito 9 (RF03)."""
    numero = so_digitos(celular)

    if len(numero) != 11:
        return False
    if not 11 <= int(numero[:2]) <= 99:  # DDD valido comeca em 11
        return False
    return numero[2] == "9"


def validar_data_nascimento(data_nascimento, hoje=None):
    """Exige data passada e idade minima de 18 anos.

    `hoje` e injetavel para que o teste nao dependa da data em que roda.
    """
    if data_nascimento is None:
        return False

    hoje = hoje or date.today()
    if data_nascimento >= hoje:
        return False

    idade = hoje.year - data_nascimento.year
    # Ainda nao fez aniversario este ano.
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1

    return idade >= IDADE_MINIMA


def parse_data(valor):
    """Converte 'AAAA-MM-DD' em date. Devolve None se o formato for invalido."""
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None
