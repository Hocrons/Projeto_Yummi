"""
Cálculo de distância e taxa de entrega.

Duas responsabilidades:
  1. calcular_distancia_km(lat1, lon1, lat2, lon2) -> Haversine (linha reta)
  2. calcular_taxa_entrega(taxa_base, distancia_km) -> aplica a regra

Regra de taxa:
  - distância <= 5 km      -> taxa base do restaurante
  - distância > 5 km       -> taxa base + R$ 1 por km que exceder 5
                              ex: base 5 + dist 8 = 5 + (8-5)*1 = R$ 8
Nenhuma query SQL mora aqui — só a matemática.
"""
import math

# Distância (em km) a partir da qual começa a cobrar por km extra
LIMITE_KM = 5.0

# Valor cobrado por km que exceder o LIMITE_KM
VALOR_POR_KM_EXTRA = 1.0


def calcular_distancia_km(lat1, lon1, lat2, lon2):
    """
    Distância em linha reta (Haversine) entre dois pontos, em km.
    Retorna None se faltar alguma coordenada.
    """
    if None in (lat1, lon1, lat2, lon2):
        return None
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (TypeError, ValueError):
        return None

    raio_terra_km = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return raio_terra_km * c


def calcular_taxa_entrega(taxa_base, distancia_km):
    """
    Aplica a regra da taxa:
      - Sem distância  -> devolve só a taxa base.
      - <= 5 km        -> taxa base.
      - > 5 km         -> taxa base + R$ 1 por km extra (acima de 5).

    Retorna (taxa_total, distancia_km, km_extra)
      - taxa_total: float, com 2 casas
      - distancia_km: float ou None
      - km_extra: float (0.0 se não passou do limite)
    """
    try:
        taxa_base = float(taxa_base or 0)
    except (TypeError, ValueError):
        taxa_base = 0.0

    if distancia_km is None:
        return round(taxa_base, 2), None, 0.0

    if distancia_km <= LIMITE_KM:
        return round(taxa_base, 2), round(distancia_km, 2), 0.0

    km_extra = distancia_km - LIMITE_KM
    taxa_total = taxa_base + (km_extra * VALOR_POR_KM_EXTRA)
    return round(taxa_total, 2), round(distancia_km, 2), round(km_extra, 2)