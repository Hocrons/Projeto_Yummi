"""Model USUARIO - camada M do MVC.

Espelha campo a campo o dicionario de dados da secao 8 de YUMMI_PROJETO.md.
Uma linha por pessoa com login; `tipo_usuario` define o papel, evitando quatro
tabelas com os mesmos campos de identificacao.
"""
from datetime import date, datetime

from sqlalchemy import CHAR, CheckConstraint, Date, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db

# Dominios dos campos de texto controlado.
TIPOS_USUARIO = ("cliente", "restaurante", "entregador", "admin")
STATUS_CONTA = ("pendente", "ativo", "bloqueado", "excluido")
PROVEDORES_SOCIAIS = ("google", "facebook")


def _dominio(coluna, valores):
    """Monta a expressao SQL `coluna IN (...)` a partir de uma tupla Python."""
    lista = ",".join(f"'{v}'" for v in valores)
    return f"{coluna} IN ({lista})"


class Usuario(db.Model):
    __tablename__ = "USUARIO"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(100), nullable=False)
    # Nulo quando o cadastro foi feito so por celular, e vice-versa.
    email: Mapped[str | None] = mapped_column(String(254), nullable=True, unique=True)
    celular: Mapped[str | None] = mapped_column(String(15), nullable=True, unique=True)
    cpf: Mapped[str] = mapped_column(CHAR(11), nullable=False, unique=True)
    # Preenchido apenas para responsavel de restaurante.
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    # Nulo quando o acesso e somente por Google/Facebook.
    senha_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tipo_usuario: Mapped[str] = mapped_column(String(20), nullable=False, server_default="cliente")
    status_conta: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pendente")
    provedor_social: Mapped[str | None] = mapped_column(String(20), nullable=True)
    id_social: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        CheckConstraint(_dominio("tipo_usuario", TIPOS_USUARIO), name="tipo"),
        CheckConstraint(_dominio("status_conta", STATUS_CONTA), name="status"),
        CheckConstraint(
            f"provedor_social IS NULL OR {_dominio('provedor_social', PROVEDORES_SOCIAIS)}",
            name="provedor",
        ),
        # Cadastro exige ao menos um identificador de contato (RF02/RF03).
        CheckConstraint("email IS NOT NULL OR celular IS NOT NULL", name="contato"),
        # Senha so pode faltar quando o acesso e por login social (RF05/RF09).
        CheckConstraint(
            "senha_hash IS NOT NULL OR provedor_social IS NOT NULL", name="senha"
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    def to_dict(self):
        """Serializacao publica do usuario.

        `senha_hash` e `id_social` nunca saem daqui - nao ha rota que os exponha.
        """
        return {
            "id_usuario": self.id_usuario,
            "nome_completo": self.nome_completo,
            "email": self.email,
            "celular": self.celular,
            "cpf": self.cpf,
            "rg": self.rg,
            "data_nascimento": self.data_nascimento.isoformat() if self.data_nascimento else None,
            "tipo_usuario": self.tipo_usuario,
            "status_conta": self.status_conta,
            "provedor_social": self.provedor_social,
            "data_cadastro": self.data_cadastro.isoformat() if self.data_cadastro else None,
        }

    def __repr__(self):
        return f"<Usuario {self.id_usuario} {self.nome_completo!r} {self.status_conta}>"
