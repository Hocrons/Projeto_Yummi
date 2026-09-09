"""
Models do sistema Yummy.
Cada função representa uma operação no banco (Model, no padrão MVC).
Nenhuma lógica de rota/HTTP entra aqui - isso fica nos controllers.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import DB


# =========================================================
# USUARIO (base de cliente / restaurante / entregador)
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
    """
    Busca por telefone já normalizado (ver utils.normalizar_telefone).
    Usado no fluxo de login/cadastro passwordless por celular.
    """
    with DB() as db:
        db.cursor.execute("SELECT * FROM usuario WHERE telefone=%s", (telefone_normalizado,))
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
def criar_cliente(id_usuario, cpf, apelido):
    with DB() as db:
        db.cursor.execute(
            "INSERT INTO cliente (id_usuario, cpf, apelido) VALUES (%s, %s, %s)",
            (id_usuario, cpf, apelido),
        )


def buscar_cliente(id_usuario):
    with DB() as db:
        db.cursor.execute(
            """SELECT u.*, c.cpf, c.apelido
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


# =========================================================
# RESTAURANTE
# =========================================================
def criar_restaurante(id_usuario, nome_fantasia, cnpj, categoria, taxa_entrega,
                       horario_funcionamento, rua, numero, bairro, cidade, cep):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO restaurante
               (id_usuario, nome_fantasia, cnpj, categoria, taxa_entrega,
                horario_funcionamento, rua, numero, bairro, cidade, cep)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (id_usuario, nome_fantasia, cnpj, categoria, taxa_entrega,
             horario_funcionamento, rua, numero, bairro, cidade, cep),
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
                      r.horario_funcionamento, r.rua, r.numero, r.bairro, r.cidade, r.cep
               FROM usuario u JOIN restaurante r ON r.id_usuario = u.id
               WHERE u.id=%s""",
            (id_usuario,),
        )
        return db.cursor.fetchone()


def atualizar_restaurante(id_usuario, nome_fantasia, categoria, taxa_entrega,
                           horario_funcionamento, rua, numero, bairro, cidade, cep):
    with DB() as db:
        db.cursor.execute(
            """UPDATE restaurante SET nome_fantasia=%s, categoria=%s, taxa_entrega=%s,
               horario_funcionamento=%s, rua=%s, numero=%s, bairro=%s, cidade=%s, cep=%s
               WHERE id_usuario=%s""",
            (nome_fantasia, categoria, taxa_entrega, horario_funcionamento,
             rua, numero, bairro, cidade, cep, id_usuario),
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
def criar_produto(id_restaurante, nome, descricao, preco, disponivel=True):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO produto (id_restaurante, nome, descricao, preco, disponivel)
               VALUES (%s,%s,%s,%s,%s)""",
            (id_restaurante, nome, descricao, preco, disponivel),
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


def atualizar_produto(id_produto, nome, descricao, preco, disponivel):
    with DB() as db:
        db.cursor.execute(
            """UPDATE produto SET nome=%s, descricao=%s, preco=%s, disponivel=%s
               WHERE id=%s""",
            (nome, descricao, preco, disponivel, id_produto),
        )


def deletar_produto(id_produto):
    with DB() as db:
        db.cursor.execute("DELETE FROM produto WHERE id=%s", (id_produto,))


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
    """Retorna apenas os endereços ativos do cliente."""
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
    """Só atualiza se o endereço pertencer ao cliente logado (id_cliente)."""
    with DB() as db:
        db.cursor.execute(
            """UPDATE endereco SET rua=%s, numero=%s, bairro=%s, cidade=%s, cep=%s
               WHERE id=%s AND id_cliente=%s""",
            (rua, numero, bairro, cidade, cep, id_endereco, id_cliente),
        )
        return db.cursor.rowcount > 0


def deletar_endereco(id_endereco, id_cliente):
    """Realiza exclusão lógica (soft delete) para evitar o erro de chave estrangeira com pedidos."""
    with DB() as db:
        db.cursor.execute(
            "UPDATE endereco SET ativo = 0 WHERE id=%s AND id_cliente=%s",
            (id_endereco, id_cliente),
        )
        return db.cursor.rowcount > 0


# =========================================================
# PEDIDO / ITEM_PEDIDO / PAGAMENTO
# =========================================================
def criar_pedido_completo(id_cliente, id_restaurante, id_endereco, itens, forma_pagamento):
    """
    itens: lista de dicts [{id_produto, quantidade, preco_unitario}, ...]
    Cria pedido + itens + pagamento numa única transação.

    Validação de segurança: garante que TODOS os produtos pertencem ao
    mesmo restaurante (id_restaurante) antes de gravar qualquer coisa,
    mesmo que o carrinho já tenha bloqueado isso na camada de sessão.
    Isso evita que alguém manipule a requisição e misture pedidos de
    restaurantes diferentes.
    """
    if not itens:
        raise ValueError("O pedido precisa ter pelo menos um item.")

    with DB() as db:
        ids_produto = [i["id_produto"] for i in itens]
        formato = ",".join(["%s"] * len(ids_produto))
        db.cursor.execute(
            f"SELECT id, id_restaurante FROM produto WHERE id IN ({formato})",
            ids_produto,
        )
        produtos_encontrados = db.cursor.fetchall()

        if len(produtos_encontrados) != len(set(ids_produto)):
            raise ValueError("Um ou mais produtos do pedido não foram encontrados.")

        for p in produtos_encontrados:
            if p["id_restaurante"] != id_restaurante:
                raise ValueError(
                    "Não é possível fazer um pedido com produtos de restaurantes diferentes."
                )

        valor_total = sum(i["quantidade"] * float(i["preco_unitario"]) for i in itens)

        db.cursor.execute(
            """INSERT INTO pedido (id_cliente, id_restaurante, id_endereco, status, valor_total)
               VALUES (%s,%s,%s,'pendente',%s)""",
            (id_cliente, id_restaurante, id_endereco, valor_total),
        )
        id_pedido = db.cursor.lastrowid

        for item in itens:
            db.cursor.execute(
                """INSERT INTO item_pedido (id_pedido, id_produto, quantidade, preco_unitario)
                   VALUES (%s,%s,%s,%s)""",
                (id_pedido, item["id_produto"], item["quantidade"], item["preco_unitario"]),
            )

        db.cursor.execute(
            """INSERT INTO pagamento (id_pedido, forma_pagamento, valor, status)
               VALUES (%s,%s,%s,'pendente')""",
            (id_pedido, forma_pagamento, valor_total),
        )
        return id_pedido


def buscar_pedido(id_pedido):
    with DB() as db:
        db.cursor.execute(
            """SELECT p.*, r.nome_fantasia, uc.nome AS nome_cliente,
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
            """SELECT p.*, r.nome_fantasia
               FROM pedido p JOIN restaurante r ON r.id_usuario = p.id_restaurante
               WHERE p.id_cliente=%s ORDER BY p.data_hora DESC""",
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
    """Pedidos prontos, aguardando algum entregador aceitar (sem entregador atribuído)."""
    with DB() as db:
        db.cursor.execute(
            """SELECT p.*, r.nome_fantasia, r.rua AS rua_restaurante,
                      r.bairro AS bairro_restaurante, e.rua AS rua_entrega, e.bairro AS bairro_entrega
               FROM pedido p
               JOIN restaurante r ON r.id_usuario = p.id_restaurante
               LEFT JOIN endereco e ON e.id = p.id_endereco
               WHERE p.status='localizando_entregador' AND p.id_entregador IS NULL
               ORDER BY p.data_hora"""
        )
        return db.cursor.fetchall()


def listar_pedidos_entregador(id_entregador, apenas_ativos=False):
    query = """SELECT p.*, r.nome_fantasia, r.rua AS rua_restaurante, r.bairro AS bairro_restaurante,
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
    """
    Entregador aceita a corrida: só funciona se o pedido ainda estiver
    'localizando_entregador' e sem ninguém atribuído (evita corrida entre
    dois entregadores aceitando ao mesmo tempo).
    """
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET id_entregador=%s, status='indo_ao_restaurante'
               WHERE id=%s AND id_entregador IS NULL AND status='localizando_entregador'""",
            (id_entregador, id_pedido),
        )
        return db.cursor.rowcount > 0


def marcar_pedido_retirado(id_pedido, id_entregador):
    """Entregador confirma que retirou o pedido no restaurante e saiu para entregar."""
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET status='saiu_para_entrega'
               WHERE id=%s AND id_entregador=%s AND status='indo_ao_restaurante'""",
            (id_pedido, id_entregador),
        )
        return db.cursor.rowcount > 0


def marcar_pedido_entregue(id_pedido, id_entregador):
    """Entregador confirma a entrega. Só permite se a corrida for dele mesmo."""
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET status='entregue'
               WHERE id=%s AND id_entregador=%s AND status='saiu_para_entrega'""",
            (id_pedido, id_entregador),
        )
        return db.cursor.rowcount > 0


def liberar_entregador(id_pedido, id_restaurante):
    """
    Restaurante troca de entregador: só é permitido enquanto o entregador
    ainda está a caminho do restaurante (ainda não retirou o pedido).
    O pedido volta para a fila de 'localizando_entregador'.
    """
    with DB() as db:
        db.cursor.execute(
            """UPDATE pedido SET id_entregador=NULL, status='localizando_entregador'
               WHERE id=%s AND id_restaurante=%s AND status='indo_ao_restaurante'""",
            (id_pedido, id_restaurante),
        )
        return db.cursor.rowcount > 0


def atualizar_status_pedido(id_pedido, status, id_restaurante=None):
    """
    Atualiza o status do pedido. Quando id_restaurante é informado, só
    atualiza se o pedido pertencer àquele restaurante (evita um restaurante
    mexer no pedido de outro).
    """
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