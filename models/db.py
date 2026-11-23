"""
Camada de acesso ao banco de dados MySQL.
Toda conexão passa por aqui para manter o resto do app (controllers e
models) desacoplado do driver de banco usado (PyMySQL).
"""
import os
from urllib.parse import parse_qs, unquote, urlsplit
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

def _database_config():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlsplit(database_url)
        if parsed.scheme not in {"mysql", "mysql+pymysql"}:
            raise ValueError(
                "DATABASE_URL precisa usar uma conexão MySQL compatível com PyMySQL."
            )
        if not parsed.hostname or not parsed.path.strip("/"):
            raise ValueError("DATABASE_URL precisa informar host e nome do banco.")

        query = parse_qs(parsed.query)
        config = {
            "host": parsed.hostname,
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "database": unquote(parsed.path.lstrip("/")),
            "charset": query.get("charset", ["utf8mb4"])[0],
            "cursorclass": pymysql.cursors.DictCursor,
            "autocommit": False,
        }
        ssl_mode = (
            query.get("ssl-mode")
            or query.get("ssl_mode")
            or query.get("sslmode")
            or [""]
        )[0].strip().lower().replace("_", "-")
        if ssl_mode in {"required", "verify-ca", "verify-identity", "verify-full"}:
            ssl_options = {}
            if ssl_mode != "required":
                ssl_options["verify_mode"] = "required"
                ssl_options["check_hostname"] = ssl_mode in {
                    "verify-identity",
                    "verify-full",
                }
            ssl_ca = query.get("ssl-ca") or query.get("ssl_ca")
            if ssl_ca:
                ssl_options["ca"] = unquote(ssl_ca[0])
            config["ssl"] = ssl_options
        elif ssl_mode and ssl_mode not in {"disabled", "disable", "preferred"}:
            raise ValueError(
                f"Modo SSL não suportado em DATABASE_URL: {ssl_mode}."
            )
        return config

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "yummy"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }


DB_CONFIG = _database_config()


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
