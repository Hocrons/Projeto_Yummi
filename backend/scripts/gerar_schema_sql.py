"""Gera o modelo fisico em SQL a partir dos models SQLAlchemy.

Por que existe: a disciplina cobra um modelo de dados fisico com tipos, campos
nulos e nao nulos, chaves e FKs. Escrever esse SQL a mao em paralelo aos models
cria duas fontes que divergem. Aqui o SQL e derivado dos models, entao os dois
nunca saem de sincronia.

Uso:
    python scripts/gerar_schema_sql.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from sqlalchemy.dialects import mysql  # noqa: E402
from sqlalchemy.schema import CreateIndex, CreateTable  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

DESTINO = RAIZ / "database" / "yummi_schema.sql"

CABECALHO = """-- =====================================================================
-- Yummi - Modelo de dados fisico
-- MySQL 8.0+
--
-- ARQUIVO GERADO. Nao edite a mao.
-- Fonte: os models SQLAlchemy em backend/app/models/.
-- Para regenerar:  python scripts/gerar_schema_sql.py
-- =====================================================================

DROP DATABASE IF EXISTS yummi;
CREATE DATABASE yummi
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE yummi;
"""


def gerar_sql():
    # create_app importa os models, que e o que popula o metadata.
    create_app()
    dialeto = mysql.dialect()
    partes = [CABECALHO]

    # sorted_tables ordena por dependencia: nenhuma FK aponta para tabela
    # que ainda nao foi criada.
    for tabela in db.metadata.sorted_tables:
        partes.append(f"\n-- ---------------------------------------------- {tabela.name}")
        ddl = str(CreateTable(tabela).compile(dialect=dialeto)).strip()
        partes.append(f"{ddl};\n")
        for indice in tabela.indexes:
            partes.append(str(CreateIndex(indice).compile(dialect=dialeto)).strip() + ";")

    return "\n".join(partes) + "\n"


def main():
    sql = gerar_sql()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(sql, encoding="utf-8")

    tabelas = list(db.metadata.sorted_tables)
    campos = sum(len(t.columns) for t in tabelas)
    fks = sum(len(t.foreign_keys) for t in tabelas)

    print(f"Escrito: {DESTINO}")
    print(f"{len(tabelas)} tabelas | {campos} campos | {fks} chaves estrangeiras")


if __name__ == "__main__":
    main()
