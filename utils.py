"""
Funções utilitárias usadas por vários módulos (controllers e services).
"""
import re


def normalizar_telefone(telefone, ddi_padrao="55"):
    """
    Converte um telefone em qualquer formato (ex: "(11) 99999-9999") para
    uma forma normalizada de apenas dígitos, com DDI, sem o "+"
    (ex: "5511999999999"). Usada tanto para salvar quanto para consultar
    telefones no banco, garantindo que a comparação seja sempre consistente.
    """
    numeros = re.sub(r"\D", "", telefone or "")
    if not numeros:
        return ""
    if not numeros.startswith(ddi_padrao):
        numeros = ddi_padrao + numeros
    return numeros


def mascarar_email(email):
    """'thiagosilva@gmail.com' -> '*********va@gmail.com'"""
    if not email or "@" not in email:
        return email or ""
    local, dominio = email.split("@", 1)
    if len(local) <= 2:
        return f"{local}@{dominio}"
    visivel = local[-2:]
    mascara = "*" * (len(local) - 2)
    return f"{mascara}{visivel}@{dominio}"


def mascarar_telefone(telefone_normalizado):
    """'5511959913833' -> '(11) ***** - 3833'"""
    digitos = telefone_normalizado or ""
    if len(digitos) < 6:
        return telefone_normalizado or ""
    ddd = digitos[2:4]
    ultimos4 = digitos[-4:]
    return f"({ddd}) ***** - {ultimos4}"