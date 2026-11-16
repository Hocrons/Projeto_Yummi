"""
========================================================
  YUMMI — Funções de Model para adicionar em models/models.py
========================================================
"""

# =========================================================
# PRODUTO — adicionar / complementar em models/models.py
# =========================================================

def listar_produtos_restaurante(id_restaurante):
    with DB() as db:
        db.cursor.execute(
            "SELECT * FROM produto WHERE id_restaurante=%s ORDER BY nome",
            (id_restaurante,),
        )
        return db.cursor.fetchall()


def buscar_produto(id_produto):
    with DB() as db:
        db.cursor.execute("SELECT * FROM produto WHERE id=%s", (id_produto,))
        return db.cursor.fetchone()


def criar_produto(id_restaurante, nome, descricao, preco, disponivel=True, foto_url=None):
    with DB() as db:
        db.cursor.execute(
            """INSERT INTO produto (id_restaurante, nome, descricao, preco, disponivel, foto_url)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (id_restaurante, nome, descricao, preco, disponivel, foto_url),
        )
        return db.cursor.lastrowid


def atualizar_produto(produto_id, nome, descricao, preco, disponivel, foto_url):
    with DB() as db:
        db.cursor.execute(
            """UPDATE produto
               SET nome=%s, descricao=%s, preco=%s, disponivel=%s, foto_url=%s
               WHERE id=%s""",
            (nome, descricao, preco, disponivel, foto_url, produto_id),
        )


def deletar_produto(produto_id):
    with DB() as db:
        db.cursor.execute("DELETE FROM produto WHERE id=%s", (produto_id,))


# =========================================================
# RESTAURANTE — buscar_restaurante já existe, confirme:
# =========================================================

def buscar_restaurante(id_usuario):
    with DB() as db:
        db.cursor.execute(
            """SELECT r.*, u.nome, u.email, u.telefone
               FROM restaurante r JOIN usuario u ON u.id = r.id_usuario
               WHERE r.id_usuario=%s""",
            (id_usuario,),
        )
        return db.cursor.fetchone()
