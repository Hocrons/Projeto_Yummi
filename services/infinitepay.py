"""Cliente HTTP do checkout hospedado da InfinitePay."""
import os
from urllib.parse import urlsplit

import requests


API_URL = "https://api.checkout.infinitepay.io"
TIMEOUT_SECONDS = 20


class InfinitePayError(Exception):
    """Falha ao criar ou consultar um checkout da InfinitePay."""


def obter_handle():
    handle = os.getenv("INFINITEPAY_HANDLE", "").strip()
    if not handle:
        raise InfinitePayError(
            "Configure INFINITEPAY_HANDLE no arquivo .env para receber pagamentos."
        )
    return handle


def obter_base_url_publica():
    base_url = os.getenv("BASE_URL", "http://localhost:5000").strip().rstrip("/")
    parsed = urlsplit(base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise InfinitePayError("Configure BASE_URL com a URL pública do site.")

    if os.getenv("FLASK_DEBUG", "1") != "1" and parsed.scheme != "https":
        raise InfinitePayError("BASE_URL precisa usar HTTPS em produção.")
    return base_url


def criar_link_pagamento(handle, order_nsu, valor_centavos, descricao,
                         redirect_url, webhook_url):
    payload = {
        "handle": handle,
        "order_nsu": order_nsu,
        "redirect_url": redirect_url,
        "webhook_url": webhook_url,
        "items": [{
            "description": descricao,
            "quantity": 1,
            "price": valor_centavos,
        }],
    }

    try:
        response = requests.post(
            f"{API_URL}/links",
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as erro:
        raise InfinitePayError(
            "Não foi possível conectar à InfinitePay. Tente novamente."
        ) from erro

    if not response.ok:
        raise InfinitePayError(
            f"A InfinitePay não criou o link de pagamento (HTTP {response.status_code})."
        )

    try:
        dados = response.json()
    except ValueError as erro:
        raise InfinitePayError("A InfinitePay retornou uma resposta inválida.") from erro

    if not isinstance(dados, dict) or dados.get("success") is False:
        raise InfinitePayError("A InfinitePay não conseguiu criar o link de pagamento.")

    checkout_url = dados.get("url")
    parsed_url = urlsplit(checkout_url or "")
    if (
        parsed_url.scheme != "https"
        or not parsed_url.hostname
        or not (
            parsed_url.hostname == "infinitepay.io"
            or parsed_url.hostname.endswith(".infinitepay.io")
        )
    ):
        raise InfinitePayError("A InfinitePay retornou um endereço de checkout inválido.")

    return checkout_url


def verificar_pagamento(handle, order_nsu, transaction_nsu, slug):
    try:
        response = requests.post(
            f"{API_URL}/payment_check",
            json={
                "handle": handle,
                "order_nsu": order_nsu,
                "transaction_nsu": transaction_nsu,
                "slug": slug,
            },
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as erro:
        raise InfinitePayError(
            "Não foi possível consultar a confirmação do pagamento."
        ) from erro

    if not response.ok:
        raise InfinitePayError(
            f"A InfinitePay não confirmou o pagamento (HTTP {response.status_code})."
        )

    try:
        dados = response.json()
    except ValueError as erro:
        raise InfinitePayError("A InfinitePay retornou uma resposta inválida.") from erro

    if not isinstance(dados, dict) or dados.get("success") is False:
        raise InfinitePayError("A InfinitePay não conseguiu verificar o pagamento.")
    return dados
