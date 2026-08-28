"""
Camada de acesso ao banco de dados MySQL.
Toda conexão passa por aqui para manter o resto do app (controllers e
models) desacoplado do driver de banco usado (PyMySQL).
"""
import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "yummy"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}


def get_connection():
    """Abre uma nova conexão com o MySQL. Chame connection.close() depois."""
    return pymysql.connect(**DB_CONFIG)


class DB:
    """
    Context manager simples para não repetir try/finally em todo model.

    Uso:
        with DB() as db:
            db.cursor.execute("SELECT * FROM usuario WHERE id=%s", (1,))
            row = db.cursor.fetchone()
    """

    def __enter__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cursor.close()
        self.conn.close()
        # não suprime exceções
        return False
