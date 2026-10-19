"""Migrações incrementais do schema MySQL."""


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
