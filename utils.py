"""
Funções utilitárias usadas por vários módulos (controllers e services).
"""
import re


def normalizar_telefone(telefone, ddi_padrao="55"):
    """
    Normaliza um telefone brasileiro para o formato DDI + DDD + número,
    somente dígitos (ex: "5511959913833").

    Aceita entradas como:
      "(11) 99999-9999"     -> "5511999999999"
      "11999999999"         -> "5511999999999"
      "5511999999999"       -> "5511999999999"  (já normalizado)
      "+55 11 99999-9999"   -> "5511999999999"

    Rejeita (retorna "") se o número não parecer brasileiro válido.
    """
    numeros = re.sub(r"\D", "", telefone or "")
    if not numeros:
        return ""

    ddi = re.sub(r"\D", "", ddi_padrao or "55") or "55"

    # Caso 1: já começa com o DDI (13 ou 12 dígitos com DDI)
    #   ex: 5511959913833 (13) ou 551135551234 (12)
    if numeros.startswith(ddi):
        resto = numeros[len(ddi):]
        if 10 <= len(resto) <= 11:
            return ddi + resto
        # Se tiver tamanho estranho (ex: "55" + 8 dígitos), cai no fluxo abaixo
        # como se NÃO tivesse DDI, pra tentar consertar.

    # Caso 2: 11 dígitos -> DDD (2) + celular (9)
    if len(numeros) == 11:
        return ddi + numeros

    # Caso 3: 10 dígitos -> DDD (2) + fixo (8)
    if len(numeros) == 10:
        return ddi + numeros

    # Caso 4: 9 dígitos -> celular sem DDD. NÃO dá pra adivinhar o DDD.
    # Aqui devolvemos "" (inválido) para o formulário pedir DDD de novo.
    if len(numeros) == 9:
        return ""

    # Caso 5: 8 dígitos -> fixo sem DDD. Mesmo problema do caso 4.
    if len(numeros) == 8:
        return ""

    # Qualquer outro tamanho: inválido.
    return ""


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