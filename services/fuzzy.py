"""
Busca por aproximação (fuzzy) para nomes de produtos.

Usado quando o cliente digita algo com erro de digitação
(ex: "yakisoba" quando o produto cadastrado é "Yakissoba").

Estratégia:
- O models.buscar_produtos_por_nome faz o LIKE tradicional no banco (rápido).
- Se o LIKE trouxe poucos resultados, este módulo ajuda a pescar produtos
  parecidos usando similaridade (rapidfuzz) sobre uma lista de candidatos.

Nenhuma query SQL mora aqui — só a lógica de ranquear e filtrar.
"""
from rapidfuzz import fuzz

# Limiar mínimo de similaridade (0-100). Abaixo disso, descarta.
# 70 = aceita erros tipo "yakisoba" vs "yakissoba" (93%) e "piza" vs "pizza" (89%).
LIMIAR_PADRAO = 70


def _normalizar(texto):
    """Minúsculas + sem espaços extras. Não mexe em acentos (o rapidfuzz já lida bem)."""
    return (texto or "").strip().lower()


def ranquear_produtos(termo, produtos, limiar=LIMIAR_PADRAO, limite=60):
    """
    Recebe um termo de busca e uma lista de dicts de produtos
    (cada um com pelo menos 'nome_produto'), e devolve a lista
    ordenada por similaridade, filtrando os que passam do limiar.

    Além do nome do produto, também considera a descrição (com peso menor).
    """
    termo_norm = _normalizar(termo)
    if not termo_norm:
        return []

    pontuados = []
    for p in produtos:
        nome = _normalizar(p.get("nome_produto"))
        desc = _normalizar(p.get("descricao_produto") or "")

        # Similaridade pelo nome (peso cheio)
        sim_nome = fuzz.partial_ratio(termo_norm, nome)

        # Similaridade pela descrição (peso reduzido, e só se a descrição existir)
        sim_desc = fuzz.partial_ratio(termo_norm, desc) if desc else 0

        # Nota final: nome vale mais
        nota = max(sim_nome, sim_desc * 0.7)

        if nota >= limiar:
            pontuados.append((nota, p))

    # Ordena da maior nota pra menor e devolve só os dicts
    pontuados.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in pontuados[:limite]]