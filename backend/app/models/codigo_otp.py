"""Model CODIGO_OTP - camada M do MVC.

Espelha o dicionario de dados da secao 8 de YUMMI_PROJETO.md. Guardamos o
historico completo de codigos enviados, e nao apenas o ultimo: e o historico
que permite auditar tentativas e barrar abuso (RF04/RF10).
"""
from datetime import datetime

from sqlalchemy import CHAR, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

CANAIS = ("whatsapp", "sms", "email")
FINALIDADES = ("cadastro", "login")

# RF04: 5 minutos de validade, no maximo 5 tentativas, reenvio so apos 60s.
VALIDADE_MINUTOS = 5
MAX_TENTATIVAS = 5
INTERVALO_REENVIO_SEGUNDOS = 60


def _dominio(coluna, valores):
    """Monta a expressao SQL `coluna IN (...)` a partir de uma tupla Python."""
    lista = ",".join(f"'{v}'" for v in valores)
    return f"{coluna} IN ({lista})"


class CodigoOtp(db.Model):
    __tablename__ = "CODIGO_OTP"

    id_otp: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("USUARIO.id_usuario"), nullable=False, index=True
    )
    codigo: Mapped[str] = mapped_column(CHAR(6), nullable=False)
    canal: Mapped[str] = mapped_column(String(20), nullable=False)
    finalidade: Mapped[str] = mapped_column(String(20), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tentativas: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    validado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))

    usuario = relationship("Usuario", backref="codigos_otp")

    __table_args__ = (
        CheckConstraint(_dominio("canal", CANAIS), name="canal"),
        CheckConstraint(_dominio("finalidade", FINALIDADES), name="finalidade"),
        # LENGTH em vez de REGEXP: o REGEXP do MySQL nao existe no SQLite, que
        # e o banco usado pelos testes. A garantia de que sao digitos vem de
        # quem gera o codigo, no otp_service.
        CheckConstraint("LENGTH(codigo) = 6", name="codigo"),
        CheckConstraint(f"tentativas BETWEEN 0 AND {MAX_TENTATIVAS}", name="tentativas"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    def expirado(self, agora=None):
        return (agora or datetime.now()) > self.expira_em

    def esgotou_tentativas(self):
        return self.tentativas >= MAX_TENTATIVAS

    def utilizavel(self, agora=None):
        """Codigo ainda vale: nao foi usado, nao expirou e tem tentativa sobrando."""
        return not self.validado and not self.expirado(agora) and not self.esgotou_tentativas()

    def __repr__(self):
        return f"<CodigoOtp {self.id_otp} usuario={self.id_usuario} validado={self.validado}>"
