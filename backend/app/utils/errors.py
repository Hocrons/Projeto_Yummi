"""Erros de negocio e formato unico de resposta JSON de erro."""


class ErroDeValidacao(Exception):
    """Dado enviado pelo cliente e invalido. Vira HTTP 400."""

    def __init__(self, campo, mensagem):
        self.campo = campo
        self.mensagem = mensagem
        super().__init__(f"{campo}: {mensagem}")


class ErroDeConflito(Exception):
    """Viola uma regra de unicidade (RF08). Vira HTTP 409."""

    def __init__(self, campo, mensagem):
        self.campo = campo
        self.mensagem = mensagem
        super().__init__(f"{campo}: {mensagem}")


class NaoEncontrado(Exception):
    """Recurso inexistente. Vira HTTP 404."""
