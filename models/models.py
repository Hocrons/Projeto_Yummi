"""
Models do sistema Yummy.
Cada função representa uma operação no banco (Model, no padrão MVC).
Nenhuma lógica de rota/HTTP entra aqui - isso fica nos controllers.
"""
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import DB


def _so_digitos(txt):
    return re.sub(r"\D", "", txt or "")


# =========================================================
# USUARIO
# =========================================================
def criar_usuario(nome, email, senha, telefone, tipo):
    senha_hash = generate_password_hash(senha)
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO usuario (nome, email, senha, telefone, tipo)
               VALUES (%s, %s, %s, %s, %s)""",
            (nome, email, senha_hash, telefone, tipo),
        )
        return db.cursor.lastrowid


def buscar_usuario_por_email(email):
    with DB() as db:
        db.cursor.execute("SELECT * FROM usuario WHERE email=%s", (email,))
        return db.cursor.fetchone()


def buscar_usuario_por_id(id_usuario):
    with DB() as db:
        db.cursor.execute("SELECT * FROM usuario WHERE id=%s", (id_usuario,))
        return db.cursor.fetchone()


def buscar_usuario_por_telefone(telefone_normalizado):
    with DB() as db:
        db.cursor.execute(
            "SELECT * FROM usuario WHERE telefone=%s",
            (telefone_normalizado,),
        )
        return db.cursor.fetchone()


def buscar_usuario_por_telefone_e_tipo(telefone_normalizado, tipo):
    with DB() as db:
        db.cursor.execute(
            "SELECT * FROM usuario WHERE telefone=%s AND tipo=%s",
            (telefone_normalizado, tipo),
        )
        return db.cursor.fetchone()


def validar_login(email, senha):
    usuario = buscar_usuario_por_email(email)
    if usuario and check_password_hash(usuario["senha"], senha):
        return usuario
    return None


def atualizar_usuario(id_usuario, nome, telefone):
    with DB() as db:
        db.cursor.execute(
            "UPDATE usuario SET nome=%s, telefone=%s WHERE id=%s",
            (nome, telefone, id_usuario),
        )


# =========================================================
# CLIENTE
# =========================================================
def criar_cliente(id_usuario, cpf, apelido, codigo_entrega=None):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO cliente (id_usuario, cpf, apelido, codigo_entrega)
               VALUES (%s, %s, %s, %s)""",
            (id_usuario, cpf, apelido, codigo_entrega),
        )


def buscar_cliente(id_usuario):
    with DB() as db:
        db.cursor.execute(
            """SELECT u.*, c.cpf, c.apelido, c.codigo_entrega
               FROM usuario u JOIN cliente c ON c.id_usuario = u.id
               WHERE u.id=%s""",
            (id_usuario,),
        )
        return db.cursor.fetchone()


def atualizar_cliente(id_usuario, apelido):
    with DB() as db:
        db.cursor.execute(
            "UPDATE cliente SET apelido=%s WHERE id_usuario=%s",
            (apelido, id_usuario),
        )


def atualizar_codigo_entrega(id_usuario, codigo_entrega):
    with DB() as db:
        db.cursor.execute(
            "UPDATE cliente SET codigo_entrega=%s WHERE id_usuario=%s",
            (codigo_entrega, id_usuario),
        )


# =========================================================
# PLANO
# =========================================================
def listar_planos(apenas_ativos=True):
    query = "SELECT * FROM plano"
    if apenas_ativos:
        query += " WHERE ativo=1"
    query += " ORDER BY mensalidade DESC"
    with DB() as db:
        db.cursor.execute(query)
        return db.cursor.fetchall()


def buscar_plano(id_plano):
    with DB() as db:
        db.cursor.execute("SELECT * FROM plano WHERE id=%s", (id_plano,))
        return db.cursor.fetchone()


# =========================================================
# RESTAURANTE
# =========================================================
def criar_restaurante(id_usuario, nome_fantasia, cnpj, categoria, taxa_entrega,
                       horario_funcionamento, rua, numero, bairro, cidade, cep,
                       tem_mesa=0, complemento=None,
                       cpf_representante=None, nome_representante=None,
                       data_nasc_representante=None, id_plano=None,
                       foto_url=None):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO restaurante
               (id_usuario, nome_fantasia, cnpj, categoria, taxa_entrega,
                horario_funcionamento, rua, numero, bairro, cidade, cep,
                tem_mesa, complemento,
                cpf_representante, nome_representante, data_nasc_representante,
                id_plano, foto_url)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (id_usuario, nome_fantasia, cnpj, categoria, taxa_entrega,
             horario_funcionamento, rua, numero, bairro, cidade, cep,
             tem_mesa, complemento,
             cpf_representante, nome_representante, data_nasc_representante,
             id_plano, foto_url),
        )


def listar_restaurantes(categoria=None, busca=None):
    query = """SELECT u.id, u.nome, r.* FROM usuario u
               JOIN restaurante r ON r.id_usuario = u.id WHERE 1=1"""
    params = []
    if categoria:
        query += " AND r.categoria = %s"
        params.append(categoria)
    if busca:
        query += " AND r.nome_fantasia LIKE %s"
        params.append(f"%{busca}%")
    query += " ORDER BY r.nome_fantasia"
    with DB() as db:
        db.cursor.execute(query, params)
        return db.cursor.fetchall()


def buscar_restaurante(id_usuario):
    with DB() as db:
        db.cursor.execute(
            """SELECT u.*, r.nome_fantasia, r.cnpj, r.categoria, r.taxa_entrega,
                      r.horario_funcionamento, r.rua, r.numero, r.bairro, r.cidade, r.cep,
                      r.tem_mesa, r.complemento, r.foto_url,
                      r.cpf_representante, r.nome_representante, r.data_nasc_representante,
                      r.id_plano,
                      p.nome AS plano_nome, p.mensalidade AS plano_mensalidade,
                      p.comissao_pct AS plano_comissao_pct,
                      p.taxa_cartao_pct AS plano_taxa_cartao_pct
               FROM usuario u
               JOIN restaurante r ON r.id_usuario = u.id
               LEFT JOIN plano p ON p.id = r.id_plano
               WHERE u.id=%s""",
            (id_usuario,),
        )
        return db.cursor.fetchone()


def atualizar_restaurante(id_usuario, nome_fantasia, categoria, taxa_entrega,
                           horario_funcionamento, rua, numero, bairro, cidade, cep,
                           tem_mesa=0, complemento=None,
                           cpf_representante=None, nome_representante=None,
                           data_nasc_representante=None, id_plano=None,
                           foto_url=None):
    with DB() as db:
        db.cursor.execute(
            """UPDATE restaurante SET nome_fantasia=%s, categoria=%s, taxa_entrega=%s,
               horario_funcionamento=%s, rua=%s, numero=%s, bairro=%s, cidade=%s, cep=%s,
               tem_mesa=%s, complemento=%s,
               cpf_representante=%s, nome_representante=%s, data_nasc_representante=%s,
               id_plano=%s, foto_url=%s
               WHERE id_usuario=%s""",
            (nome_fantasia, categoria, taxa_entrega, horario_funcionamento,
             rua, numero, bairro, cidade, cep,
             tem_mesa, complemento,
             cpf_representante, nome_representante, data_nasc_representante,
             id_plano, foto_url,
             id_usuario),
        )


def atualizar_foto_restaurante(id_usuario, foto_url):
    with DB() as db:
        db.cursor.execute(
            "UPDATE restaurante SET foto_url=%s WHERE id_usuario=%s",
            (foto_url, id_usuario),
        )


def listar_categorias():
    with DB() as db:
        db.cursor.execute(
            "SELECT DISTINCT categoria FROM restaurante WHERE categoria IS NOT NULL"
        )
        return [row["categoria"] for row in db.cursor.fetchall()]


# =========================================================
# ENTREGADOR
# =========================================================
def criar_entregador(id_usuario, cpf, veiculo, placa):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO entregador (id_usuario, cpf, veiculo, placa, disponivel)
               VALUES (%s,%s,%s,%s,TRUE)""",
            (id_usuario, cpf, veiculo, placa),
        )


def buscar_entregador(id_usuario):
    with DB() as db:
        db.cursor.execute(
            """SELECT u.*, e.cpf, e.veiculo, e.placa, e.disponivel
               FROM usuario u JOIN entregador e ON e.id_usuario = u.id
               WHERE u.id=%s""",
            (id_usuario,),
        )
        return db.cursor.fetchone()


def atualizar_disponibilidade_entregador(id_usuario, disponivel):
    with DB() as db:
        db.cursor.execute(
            "UPDATE entregador SET disponivel=%s WHERE id_usuario=%s",
            (disponivel, id_usuario),
        )


# =========================================================
# PRODUTO
# =========================================================
def criar_produto(id_restaurante, nome, descricao, preco, disponivel=True, foto_url=None):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO produto (id_restaurante, nome, descricao, preco, disponivel, foto_url)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (id_restaurante, nome, descricao, preco, disponivel, foto_url),
        )
        return db.cursor.lastrowid


def listar_produtos_por_restaurante(id_restaurante, apenas_disponiveis=False):
    query = "SELECT * FROM produto WHERE id_restaurante=%s"
    if apenas_disponiveis:
        query += " AND disponivel=TRUE"
    query += " ORDER BY nome"
    with DB() as db:
        db.cursor.execute(query, (id_restaurante,))
        return db.cursor.fetchall()


def buscar_produto(id_produto):
    with DB() as db:
        db.cursor.execute("SELECT * FROM produto WHERE id=%s", (id_produto,))
        return db.cursor.fetchone()


def atualizar_produto(id_produto, nome, descricao, preco, disponivel, foto_url=None):
    with DB() as db:
        db.cursor.execute(
            """UPDATE produto SET nome=%s, descricao=%s, preco=%s, disponivel=%s, foto_url=%s
               WHERE id=%s""",
            (nome, descricao, preco, disponivel, foto_url, id_produto),
        )


def deletar_produto(id_produto):
    with DB() as db:
        db.cursor.execute("DELETE FROM produto WHERE id=%s", (id_produto,))


def _query_produtos_com_restaurante(where_sql, params, limite=200):
    query = f"""
        SELECT
            p.id              AS id_produto,
            p.nome            AS nome_produto,
            p.descricao       AS descricao_produto,
            p.preco           AS preco_produto,
            p.disponivel      AS disponivel_produto,
            p.foto_url        AS foto_produto,
            r.id_usuario      AS id_restaurante,
            r.nome_fantasia   AS nome_restaurante,
            r.categoria       AS categoria_restaurante,
            r.taxa_entrega    AS taxa_entrega,
            r.foto_url        AS foto_restaurante,
            r.bairro          AS bairro_restaurante,
            r.cidade          AS cidade_restaurante
        FROM produto p
        JOIN restaurante r ON r.id_usuario = p.id_restaurante
        WHERE p.disponivel = TRUE {where_sql}
        ORDER BY p.nome ASC
        LIMIT %s
    """
    with DB() as db:
        db.cursor.execute(query, params + [limite])
        return db.cursor.fetchall()


def buscar_produtos_por_nome(termo, limite=60):
    from services import fuzzy

    termo = (termo or "").strip()
    if not termo:
        return []

    like = f"%{termo}%"

    exatos = _query_produtos_com_restaurante(
        "AND (p.nome LIKE %s OR p.descricao LIKE %s)",
        [like, like],
        limite=limite,
    )

    if len(exatos) >= limite:
        return exatos[:limite]

    palavras = [p for p in termo.split() if len(p) >= 2]
    if not palavras:
        palavras = [termo]

    condicoes = []
    params_candidatos = []
    for palavra in palavras[:3]:
        condicoes.append("(p.nome LIKE %s OR p.descricao LIKE %s)")
        params_candidatos.extend([f"%{palavra[:3]}%", f"%{palavra[:3]}%"])

    where_candidatos = "AND (" + " OR ".join(condicoes) + ")" if condicoes else ""
    candidatos = _query_produtos_com_restaurante(
        where_candidatos,
        params_candidatos,
        limite=200,
    )

    pool = {p["id_produto"]: p for p in exatos}
    for p in candidatos:
        pool.setdefault(p["id_produto"], p)

    ranqueados = fuzzy.ranquear_produtos(termo, list(pool.values()), limiar=fuzzy.LIMIAR_PADRAO, limite=limite)

    if not ranqueados:
        return exatos[:limite]

    return ranqueados


# =========================================================
# ENDERECO
# =========================================================
def criar_endereco(id_cliente, rua, numero, bairro, cidade, cep):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO endereco (id_cliente, rua, numero, bairro, cidade, cep, ativo)
               VALUES (%s,%s,%s,%s,%s,%s, 1)""",
            (id_cliente, rua, numero, bairro, cidade, cep),
        )
        return db.cursor.lastrowid


def listar_enderecos_cliente(id_cliente):
    with DB() as db:
        db.cursor.execute(
            """SELECT * FROM endereco 
               WHERE id_cliente=%s AND (ativo = 1 OR ativo IS NULL) 
               ORDER BY id DESC""", 
            (id_cliente,)
        )
        return db.cursor.fetchall()


def buscar_endereco(id_endereco):
    with DB() as db:
        db.cursor.execute("SELECT * FROM endereco WHERE id=%s", (id_endereco,))
        return db.cursor.fetchone()


def atualizar_endereco(id_endereco, id_cliente, rua, numero, bairro, cidade, cep):
    with DB() as db:
        db.cursor.execute(
            """UPDATE endereco SET rua=%s, numero=%s, bairro=%s, cidade=%s, cep=%s
               WHERE id=%s AND id_cliente=%s""",
            (rua, numero, bairro, cidade, cep, id_endereco, id_cliente),
        )
        return db.cursor.rowcount > 0


def deletar_endereco(id_endereco, id_cliente):
    with DB() as db:
        db.cursor.execute(
            "UPDATE endereco SET ativo = 0 WHERE id=%s AND id_cliente=%s",
            (id_endereco, id_cliente),
        )
        return db.cursor.rowcount > 0


# =========================================================
# CUPOM
# =========================================================
def criar_cupom(codigo, descricao, tipo, valor,
                valor_minimo_pedido=0, valor_maximo_desconto=None,
                data_inicio=None, data_fim=None,
                limite_usos_total=None, limite_usos_por_cliente=None,
                id_restaurante=None, ativo=True):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO cupom
               (codigo, descricao, tipo, valor,
                valor_minimo_pedido, valor_maximo_desconto,
                data_inicio, data_fim,
                limite_usos_total, limite_usos_por_cliente,
                id_restaurante, ativo)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (codigo.upper().strip(), descricao, tipo, valor,
             valor_minimo_pedido, valor_maximo_desconto,
             data_inicio, data_fim,
             limite_usos_total, limite_usos_por_cliente,
             id_restaurante, ativo),
        )
        return db.cursor.lastrowid


def listar_cupons(id_restaurante=None, apenas_ativos=False):
    query = "SELECT c.*, r.nome_fantasia FROM cupom c LEFT JOIN restaurante r ON r.id_usuario = c.id_restaurante WHERE 1=1"
    params = []
    if id_restaurante is not None:
        query += " AND (c.id_restaurante = %s OR c.id_restaurante IS NULL)"
        params.append(id_restaurante)
    if apenas_ativos:
        query += " AND c.ativo = TRUE"
    query += " ORDER BY c.criado_em DESC"
    with DB() as db:
        db.cursor.execute(query, params)
        return db.cursor.fetchall()


def buscar_cupom(id_cupom):
    with DB() as db:
        db.cursor.execute("SELECT * FROM cupom WHERE id=%s", (id_cupom,))
        return db.cursor.fetchone()


def buscar_cupom_por_codigo(codigo):
    with DB() as db:
        db.cursor.execute(
            "SELECT * FROM cupom WHERE UPPER(codigo)=%s",
            (codigo.upper().strip(),),
        )
        return db.cursor.fetchone()


def atualizar_cupom(id_cupom, **campos):
    if not campos:
        return False
    sets = ", ".join(f"{k}=%s" for k in campos.keys())
    valores = list(campos.values()) + [id_cupom]
    with DB() as db:
        db.cursor.execute(f"UPDATE cupom SET {sets} WHERE id=%s", valores)
        return db.cursor.rowcount > 0


def deletar_cupom(id_cupom):
    with DB() as db:
        db.cursor.execute("DELETE FROM cupom WHERE id=%s", (id_cupom,))
        return db.cursor.rowcount > 0


def contar_usos_cupom_por_cliente(id_cupom, id_cliente):
    with DB() as db:
        db.cursor.execute(
            "SELECT COUNT(*) AS total FROM cupom_uso WHERE id_cupom=%s AND id_cliente=%s",
            (id_cupom, id_cliente),
        )
        row = db.cursor.fetchone()
        return row["total"] if row else 0


def validar_cupom(codigo, id_cliente, id_restaurante, subtotal):
    """
    Retorna (cupom_dict, valor_desconto, erro_msg).
    Se válido: (cupom, valor, None). Se inválido: (None, 0, "motivo").
    """
    cupom = buscar_cupom_por_codigo(codigo)
    if not cupom:
        return None, 0.0, "Cupom não encontrado."
    if not cupom["ativo"]:
        return None, 0.0, "Este cupom está inativo."

    agora = datetime.now()
    if cupom["data_inicio"] and agora < cupom["data_inicio"]:
        return None, 0.0, "Este cupom ainda não está válido."
    if cupom["data_fim"] and agora > cupom["data_fim"]:
        return None, 0.0, "Este cupom expirou."

    if cupom["limite_usos_total"] is not None and cupom["usos_atuais"] >= cupom["limite_usos_total"]:
        return None, 0.0, "Este cupom atingiu o limite de usos."

    if cupom["limite_usos_por_cliente"] is not None:
        usos = contar_usos_cupom_por_cliente(cupom["id"], id_cliente)
        if usos >= cupom["limite_usos_por_cliente"]:
            return None, 0.0, "Você já usou este cupom o número máximo de vezes."

    if cupom["id_restaurante"] is not None and cupom["id_restaurante"] != id_restaurante:
        return None, 0.0, "Este cupom não é válido para este restaurante."

    if float(subtotal) < float(cupom["valor_minimo_pedido"]):
        return None, 0.0, (
            f"Este cupom exige um pedido mínimo de R$ "
            f"{float(cupom['valor_minimo_pedido']):.2f}."
        )

    if cupom["tipo"] == "percentual":
        desconto = float(subtotal) * (float(cupom["valor"]) / 100.0)
    elif cupom["tipo"] == "fixo":
        desconto = float(cupom["valor"])
    else:
        return None, 0.0, "Tipo de cupom inválido."

    if cupom["valor_maximo_desconto"] is not None:
        desconto = min(desconto, float(cupom["valor_maximo_desconto"]))

    desconto = min(desconto, float(subtotal))
    return cupom, round(desconto, 2), None


def registrar_uso_cupom(id_cupom, id_cliente, id_pedido, valor_desconto):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO cupom_uso (id_cupom, id_cliente, id_pedido, valor_desconto)
               VALUES (%s,%s,%s,%s)""",
            (id_cupom, id_cliente, id_pedido, valor_desconto),
        )
        db.cursor.execute(
            "UPDATE cupom SET usos_atuais = usos_atuais + 1 WHERE id=%s",
            (id_cupom,),
        )


# =========================================================
# PEDIDO / ITEM_PEDIDO / PAGAMENTO
# =========================================================
def criar_pedido_completo(id_cliente, id_restaurante, id_endereco, itens,
                          forma_pagamento, codigo_cupom=None):
    if not itens:
        raise ValueError("O pedido precisa ter pelo menos um item.")

    with DB() as db:
        # -------- 1. Código de entrega do cliente --------
        db.cursor.execute(
            "SELECT codigo_entrega FROM cliente WHERE id_usuario=%s",
            (id_cliente,),
        )
        cli = db.cursor.fetchone()
        codigo_entrega = (cli or {}).get("codigo_entrega") if cli else None

        if not codigo_entrega:
            db.cursor.execute(
                "SELECT telefone FROM usuario WHERE id=%s",
                (id_cliente,),
            )
            u = db.cursor.fetchone()
            tel = _so_digitos((u or {}).get("telefone") or "")
            codigo_entrega = tel[-4:] if len(tel) >= 4 else None

        # -------- 2. Revalida produtos E PREÇOS no banco --------
        ids_produto = [i["id_produto"] for i in itens]
        formato = ",".join(["%s"] * len(ids_produto))
        db.cursor.execute(
            f"SELECT id, id_restaurante, preco FROM produto WHERE id IN ({formato})",
            ids_produto,
        )
        produtos_encontrados = db.cursor.fetchall()

        if len(produtos_encontrados) != len(set(ids_produto)):
            raise ValueError("Um ou mais produtos do pedido não foram encontrados.")

        precos_banco = {p["id"]: float(p["preco"]) for p in produtos_encontrados}
        for p in produtos_encontrados:
            if p["id_restaurante"] != id_restaurante:
                raise ValueError(
                    "Não é possível fazer um pedido com produtos de restaurantes diferentes."
                )

        # -------- 3. Recalcula subtotal com preço do banco --------
        subtotal = 0.0
        for item in itens:
            preco_real = precos_banco[item["id_produto"]]
            subtotal += preco_real * item["quantidade"]
        subtotal = round(subtotal, 2)

        # -------- 4. Valida cupom (se houver) --------
        id_cupom = None
        valor_desconto = 0.0
        if codigo_cupom:
            cupom, valor_desconto, erro = validar_cupom(
                codigo_cupom, id_cliente, id_restaurante, subtotal
            )
            if erro:
                raise ValueError(erro)
            id_cupom = cupom["id"]
            valor_desconto = round(valor_desconto, 2)

        valor_total = round(subtotal - valor_desconto, 2)
        if valor_total < 0:
            valor_total = 0.0

        # -------- 5. Insere o pedido --------
        db.cursor.execute(
            """INSERT INTO pedido
               (id_cliente, id_restaurante, id_endereco, status,
                valor_total, id_cupom, valor_desconto, codigo_entrega)
               VALUES (%s,%s,%s,'pendente',%s,%s,%s,%s)""",
            (id_cliente, id_restaurante, id_endereco,
             valor_total, id_cupom, valor_desconto, codigo_entrega),
        )
        id_pedido = db.cursor.lastrowid

        # -------- 6. Insere os itens (usando o preço do BANCO) --------
        for item in itens:
            db.cursor.execute(
                """INSERT INTO item_pedido (id_pedido, id_produto, quantidade, preco_unitario)
                   VALUES (%s,%s,%s,%s)""",
                (id_pedido, item["id_produto"], item["quantidade"],
                 precos_banco[item["id_produto"]]),
            )

        # -------- 7. Pagamento --------
        db.cursor.execute(
            """INSERT INTO pagamento (id_pedido, forma_pagamento, valor, status)
               VALUES (%s,%s,%s,'pendente')""",
            (id_pedido, forma_pagamento, valor_total),
        )

        # -------- 8. Registra uso do cupom --------
        if id_cupom:
            db.cursor.execute(
                """INSERT INTO cupom_uso (id_cupom, id_cliente, id_pedido, valor_desconto)
                   VALUES (%s,%s,%s,%s)""",
                (id_cupom, id_cliente, id_pedido, valor_desconto),
            )
            db.cursor.execute(
                "UPDATE cupom SET usos_atuais = usos_atuais + 1 WHERE id=%s",
                (id_cupom,),
            )

        return id_pedido


def buscar_pedido(id_pedido):
    with DB() as db:
        db.cursor.execute(
            """SELECT p.*, r.nome_fantasia, r.foto_url AS restaurante_foto_url,
                      uc.nome AS nome_cliente,
                      ue.nome AS nome_entregador
               FROM pedido p
               JOIN restaurante r ON r.id_usuario = p.id_restaurante
               JOIN usuario uc ON uc.id = p.id_cliente
               LEFT JOIN usuario ue ON ue.id = p.id_entregador
               WHERE p.id=%s""",
            (id_pedido,),
        )
        pedido = db.cursor.fetchone()
        if not pedido:
            return None
        db.cursor.execute(
            """SELECT ip.*, pr.nome AS nome_produto
               FROM item_pedido ip JOIN produto pr ON pr.id = ip.id_produto
               WHERE ip.id_pedido=%s""",
            (id_pedido,),
        )
        pedido["itens"] = db.cursor.fetchall()
        return pedido


def listar_pedidos_cliente(id_cliente):
    with DB() as db:
        db.cursor.execute(
            """SELECT p.*, r.nome_fantasia, r.foto_url AS restaurante_foto_url
               FROM pedido p JOIN restaurante r ON r.id_usuario = p.id_restaurante
               WHERE p.id_cliente=%s ORDER BY p.data_hora DESC""",
            (id_cliente,),
        )
        return db.cursor.fetchall()


def listar_pedidos_ativos_cliente(id_cliente):
    with DB() as db:
        db.cursor.execute(
            """SELECT p.id, p.status, p.valor_total, p.data_hora,
                      r.nome_fantasia
               FROM pedido p
               JOIN restaurante r ON r.id_usuario = p.id_restaurante
               WHERE p.id_cliente=%s
                 AND p.status NOT IN ('entregue', 'cancelado')
               ORDER BY p.data_hora DESC""",
            (id_cliente,),
        )
        return db.cursor.fetchall()


def listar_pedidos_restaurante(id_restaurante, status=None):
    query = """SELECT p.*, u.nome AS nome_cliente
               FROM pedido p JOIN usuario u ON u.id = p.id_cliente
               WHERE p.id_restaurante=%s"""
    params = [id_restaurante]
    if status:
        query += " AND p.status=%s"
        params.append(status)
    query += " ORDER BY p.data_hora DESC"
    with DB() as db:
        db.cursor.execute(query, params)
        return db.cursor.fetchall()


def listar_pedidos_disponiveis_para_entrega():
    with DB() as db:
        db.cursor.execute(
            """SELECT p.*, r.nome_fantasia, r.foto_url AS restaurante_foto_url,
                      r.rua AS rua_restaurante, r.bairro AS bairro_restaurante,
                      e.rua AS rua_entrega, e.bairro AS bairro_entrega
               FROM pedido p
               JOIN restaurante r ON r.id_usuario = p.id_restaurante
               LEFT JOIN endereco e ON e.id = p.id_endereco
               WHERE p.status='localizando_entregador' AND p.id_entregador IS NULL
               ORDER BY p.data_hora"""
        )
        return db.cursor.fetchall()


def listar_pedidos_entregador(id_entregador, apenas_ativos=False):
    query = """SELECT p.*, r.nome_fantasia, r.foto_url AS restaurante_foto_url,
                      r.rua AS rua_restaurante, r.bairro AS bairro_restaurante,
                      e.rua AS rua_entrega, e.bairro AS bairro_entrega
               FROM pedido p
               JOIN restaurante r ON r.id_usuario = p.id_restaurante
               LEFT JOIN endereco e ON e.id = p.id_endereco
               WHERE p.id_entregador=%s"""
    params = [id_entregador]
    if apenas_ativos:
        query += " AND p.status IN ('indo_ao_restaurante', 'saiu_para_entrega')"
    query += " ORDER BY p.data_hora DESC"
    with DB() as db:
        db.cursor.execute(query, params)
        return db.cursor.fetchall()


def atribuir_entregador(id_pedido, id_entregador):
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET id_entregador=%s, status='indo_ao_restaurante'
               WHERE id=%s AND id_entregador IS NULL AND status='localizando_entregador'""",
            (id_entregador, id_pedido),
        )
        return db.cursor.rowcount > 0


def marcar_pedido_retirado(id_pedido, id_entregador):
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET status='saiu_para_entrega'
               WHERE id=%s AND id_entregador=%s AND status='indo_ao_restaurante'""",
            (id_pedido, id_entregador),
        )
        return db.cursor.rowcount > 0


def marcar_pedido_entregue(id_pedido, id_entregador):
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET status='entregue'
               WHERE id=%s AND id_entregador=%s AND status='saiu_para_entrega'""",
            (id_pedido, id_entregador),
        )
        return db.cursor.rowcount > 0


def liberar_entregador(id_pedido, id_restaurante):
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET id_entregador=NULL, status='localizando_entregador'
               WHERE id=%s AND id_restaurante=%s AND status='indo_ao_restaurante'""",
            (id_pedido, id_restaurante),
        )
        return db.cursor.rowcount > 0


def atualizar_status_pedido(id_pedido, status, id_restaurante=None):
    with DB() as db:
        if id_restaurante is not None:
            db.cursor.execute(
                "UPDATE pedido SET status=%s WHERE id=%s AND id_restaurante=%s",
                (status, id_pedido, id_restaurante),
            )
        else:
            db.cursor.execute(
                "UPDATE pedido SET status=%s WHERE id=%s", (status, id_pedido)
            )
        return db.cursor.rowcount > 0


def atualizar_status_pagamento(id_pedido, status):
    with DB() as db:
        db.cursor.execute(
            "UPDATE pagamento SET status=%s WHERE id_pedido=%s", (status, id_pedido)
        )