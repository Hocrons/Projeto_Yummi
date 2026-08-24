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


class ErroDeAutenticacao(Exception):
    """Credencial nao confere. Vira HTTP 401.

    A mensagem e sempre a mesma para usuario inexistente e para senha errada.
    Diferenciar as duas contaria a quem esta tentando invadir se aquele e-mail
    existe na base.
    """

    def __init__(self, mensagem="E-mail ou senha incorretos."):
        self.mensagem = mensagem
        super().__init__(mensagem)


class ContaIndisponivel(Exception):
    """Credencial correta, mas a conta nao pode entrar agora. Vira HTTP 403.

    Cobre a conta pendente de verificacao (RF11) e a bloqueada por excesso de
    tentativas (RF10). Aqui a mensagem e especifica de proposito: quem chegou
    ate aqui ja provou saber a senha, e precisa saber o que fazer em seguida.
    """

    def __init__(self, mensagem, status_conta=None):
        self.mensagem = mensagem
        self.status_conta = status_conta
        super().__init__(mensagem)
