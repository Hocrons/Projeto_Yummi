"""
Geocodificação de endereços via Nominatim (OpenStreetMap).

Isola a lógica que estava duplicada em auth_ctrl.py e restaurante_ctrl.py.
Agora qualquer controller pode chamar buscar_coordenadas(...) e receber
lat/lon de um endereço textual.

Uso:
    lat, lon, endereco_usado, precisao = buscar_coordenadas(
        rua="Av. Paulista", numero="1500", bairro="Bela Vista",
        cidade="São Paulo", uf="SP"
    )
    # lat/lon são floats ou None
"""
import logging
import time
from functools import lru_cache

import pymysql
import requests

from models.db import get_connection

logger = logging.getLogger(__name__)
_REQUEST_INTERVAL_SECONDS = 1.1
_RATE_LIMIT_LOCK_NAME = "yummy_nominatim_rate_limit"


def _nominatim_search(query, limit):
    """Consulta o Nominatim com cache e limitação de taxa compartilhada."""
    connection = None
    cursor = None
    lock_acquired = False
    request_started_at = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT GET_LOCK(%s, %s) AS acquired",
            (_RATE_LIMIT_LOCK_NAME, 30),
        )
        lock_result = cursor.fetchone()
        if not lock_result or lock_result.get("acquired") != 1:
            raise requests.RequestException(
                "Não foi possível adquirir o limite global de consultas ao Nominatim."
            )
        lock_acquired = True
        request_started_at = time.monotonic()
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "format": "json",
                "limit": limit,
                "q": query,
                "countrycodes": "br",
                "addressdetails": 1,
            },
            headers={
                "User-Agent": "YummyApp/1.0 (projeto academico)",
                "Accept-Language": "pt-BR",
            },
            timeout=6,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError("Resposta inválida do serviço de geocodificação.")

        try:
            return tuple(
                (
                    float(item["lat"]),
                    float(item["lon"]),
                    item.get("display_name", ""),
                    tuple(sorted((item.get("address") or {}).items())),
                )
                for item in data
            )
        except (KeyError, TypeError) as error:
            raise ValueError("Resposta inválida do serviço de geocodificação.") from error
    except pymysql.MySQLError as error:
        raise requests.RequestException(
            "Não foi possível acessar o limite global de consultas ao Nominatim."
        ) from error
    finally:
        try:
            if cursor is not None and lock_acquired:
                wait = _REQUEST_INTERVAL_SECONDS - (time.monotonic() - request_started_at)
                if wait > 0:
                    time.sleep(wait)
                try:
                    cursor.execute(
                        "SELECT RELEASE_LOCK(%s)",
                        (_RATE_LIMIT_LOCK_NAME,),
                    )
                except pymysql.MySQLError:
                    logger.exception("Não foi possível liberar o limite global do Nominatim.")
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                finally:
                    if connection is not None:
                        connection.close()
            elif connection is not None:
                connection.close()


@lru_cache(maxsize=512)
def _cached_nominatim_search(query, limit):
    return _nominatim_search(query, limit)


def _nominatim_query(endereco):
    """Faz uma consulta simples ao Nominatim e devolve (lat, lon) ou (None, None)."""
    try:
        dados = _cached_nominatim_search(endereco, 1)
        if dados:
            return dados[0][0], dados[0][1]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        logger.exception("Falha ao geocodificar endereço.")
    return None, None


def buscar_enderecos(query):
    """Retorna sugestões de endereço para uma busca explícita do usuário."""
    rows = _cached_nominatim_search(query, 5)
    return [
        {
            "lat": lat,
            "lon": lon,
            "display_name": display_name,
            "address": dict(address),
        }
        for lat, lon, display_name, address in rows
    ]


def buscar_coordenadas(rua=None, numero=None, bairro=None, cidade=None, uf=None):
    """
    Tenta geocodificar um endereço brasileiro com várias estratégias,
    da mais específica pra mais genérica.

    Retorna (lat, lon, endereco_usado, precisao):
      - lat/lon: float ou None se nada funcionou
      - endereco_usado: string da tentativa que funcionou
      - precisao: 'rua' | 'bairro' | 'cidade' | None

    Faz uma pausa de 1.1s entre tentativas pra respeitar o rate limit
    do Nominatim (1 req/s).
    """
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

    for endereco, precisao in unicas:
        lat, lon = _nominatim_query(endereco)
        if lat is not None:
            return lat, lon, endereco, precisao

    return None, None, None, None