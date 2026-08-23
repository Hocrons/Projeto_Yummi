"""Instancias das extensoes Flask, isoladas para evitar importacao circular."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Convencao de nomes: garante que toda constraint gerada tenha nome explicito
# no SQL final (pk_, fk_, uk_, ck_, ix_), em vez de nome automatico do MySQL.
# E o que torna o schema.sql legivel como artefato de entrega.
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "uq": "uk_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


db = SQLAlchemy(model_class=Base)
