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
import time
import requests


def _nominatim_query(endereco):
    """Faz uma consulta simples ao Nominatim e devolve (lat, lon) ou (None, None)."""
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