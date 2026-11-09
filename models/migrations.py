"""Migrações incrementais do schema MySQL."""

from utils import normalizar_telefone


def _column_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table, column),
    )
    return cursor.fetchone() is not None


def _unique_indexes(cursor):
    cursor.execute(
        """
        SELECT INDEX_NAME,
               GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS indexed_columns
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'usuario'
          AND NON_UNIQUE = 0
        GROUP BY INDEX_NAME
        """
    )
    return cursor.fetchall()


def _add_role_scoped_contact_uniqueness(cursor):
    cursor.execute("SELECT id, email, telefone, tipo FROM usuario")
    usuarios = cursor.fetchall()
    normalizados = []
    emails_por_perfil = {}
    telefones_por_perfil = {}

    for usuario in usuarios:
        email = (usuario["email"] or "").strip().lower()
        telefone_original = (usuario["telefone"] or "").strip()
        telefone = normalizar_telefone(telefone_original) if telefone_original else None
        tipo = usuario["tipo"]

        if not email or "@" not in email:
            raise RuntimeError(
                "Migração bloqueada: o e-mail do usuário "
                f"{usuario['id']} é inválido. Corrija esse dado e execute "
                "db-upgrade novamente."
            )

        if telefone_original and not telefone:
            raise RuntimeError(
                "Migração bloqueada: o telefone do usuário "
                f"{usuario['id']} não pode ser normalizado. Corrija esse dado "
                "e execute db-upgrade novamente."
            )

        chave_email = (tipo, email)
        if chave_email in emails_por_perfil:
            raise RuntimeError(
                "Migração bloqueada: há e-mails duplicados no perfil "
                f"{tipo} (usuários {emails_por_perfil[chave_email]} e "
                f"{usuario['id']}). Corrija os dados antes de executar db-upgrade."
            )
        emails_por_perfil[chave_email] = usuario["id"]

        if telefone:
            chave_telefone = (tipo, telefone)
            if chave_telefone in telefones_por_perfil:
                raise RuntimeError(
                    "Migração bloqueada: há telefones duplicados no perfil "
                    f"{tipo} (usuários {telefones_por_perfil[chave_telefone]} e "
                    f"{usuario['id']}). Corrija os dados antes de executar "
                    "db-upgrade."
                )
            telefones_por_perfil[chave_telefone] = usuario["id"]

        normalizados.append((email, telefone, usuario["id"]))

    for email, telefone, id_usuario in normalizados:
        cursor.execute(
            "UPDATE usuario SET email=%s, telefone=%s WHERE id=%s",
            (email, telefone, id_usuario),
        )

    indexes = _unique_indexes(cursor)
    desired = {
        "email,tipo": "uq_usuario_email_tipo",
        "telefone,tipo": "uq_usuario_telefone_tipo",
    }

    for index in indexes:
        indexed_columns = index["indexed_columns"]
        if indexed_columns in {"email", "telefone"}:
            escaped_name = index["INDEX_NAME"].replace("`", "``")
            cursor.execute(f"ALTER TABLE `usuario` DROP INDEX `{escaped_name}`")

    existing_columns = {
        index["indexed_columns"]
        for index in _unique_indexes(cursor)
    }
    for columns, index_name in desired.items():
        if columns not in existing_columns:
            cursor.execute(
                f"ALTER TABLE `usuario` ADD UNIQUE KEY `{index_name}` ({columns})"
            )


def _add_missing_schema_columns(cursor):
    columns = (
        ("restaurante", "lat", "DECIMAL(10, 7) NULL"),
        ("restaurante", "lon", "DECIMAL(10, 7) NULL"),
        ("endereco", "lat", "DECIMAL(10, 7) NULL"),
        ("endereco", "lon", "DECIMAL(10, 7) NULL"),
        ("pedido", "taxa_entrega_cobrada", "DECIMAL(10, 2) NOT NULL DEFAULT 0"),
    )

    for table, column, definition in columns:
        if not _column_exists(cursor, table, column):
            cursor.execute(
                f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"
            )


def _add_delivery_completion_timestamp(cursor):
    if not _column_exists(cursor, "pedido", "entregue_em"):
        cursor.execute(
            "ALTER TABLE `pedido` ADD COLUMN `entregue_em` DATETIME NULL"
        )


MIGRATIONS = (
    ("001_add_missing_schema_columns", _add_missing_schema_columns),
    ("002_add_delivery_completion_timestamp", _add_delivery_completion_timestamp),
    ("003_role_scoped_contact_uniqueness", _add_role_scoped_contact_uniqueness),
)


def apply_migrations(connection):
    """Aplica migrações ainda não registradas e retorna as versões aplicadas."""
    applied_now = []
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )
        connection.commit()

        cursor.execute("SELECT version FROM schema_migrations")
        applied = {row["version"] for row in cursor.fetchall()}

        for version, migration in MIGRATIONS:
            if version in applied:
                continue

            try:
                migration(cursor)
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (version,),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            applied_now.append(version)
    finally:
        cursor.close()

    return applied_now
