"""Configuracao do Swagger UI (OpenAPI 3).

A especificacao e montada a partir das docstrings das views: o texto antes do
`---` vira o resumo do endpoint, e o YAML depois dele descreve corpo, parametros
e respostas. Os schemas que se repetem ficam aqui em `components`, para que as
docstrings so precisem referencia-los com `$ref`.

Interface publicada em /apidocs. Especificacao crua em /apispec_1.json.
"""
from flasgger import Swagger

CONFIG = {
    "openapi": "3.0.3",
    "title": "Yummi - API",
    "uiversion": 3,
    "specs": [{"endpoint": "apispec_1", "route": "/apispec_1.json"}],
    "specs_route": "/apidocs/",
}

# Exemplo usado nas respostas. O CPF e valido pelo modulo 11 e nao pertence a
# ninguem - foi gerado pelo proprio algoritmo de verificacao.
_EXEMPLO_USUARIO = {
    "id_usuario": 1,
    "nome_completo": "Maria de Souza",
    "email": "maria@exemplo.com",
    "celular": "11987654321",
    "cpf": "52998224725",
    "rg": None,
    "data_nascimento": "1998-03-15",
    "tipo_usuario": "cliente",
    "status_conta": "pendente",
    "provedor_social": None,
    "data_cadastro": "2026-08-22T20:36:42",
}

TEMPLATE = {
    "info": {
        "title": "Yummi - API de Cadastro de Usuario",
        "version": "0.1.0",
        "description": (
            "API REST do modulo de cadastro de usuario do Yummi.\n\n"
            "**Arquitetura MVC:** a rota chama o controller, que delega ao service, "
            "que fala com o model. Regra de negocio nao mora no controller e SQL nao "
            "mora no service.\n\n"
            "**Formato das respostas:** sucesso devolve `{\"dados\": ...}`; "
            "erro devolve `{\"erro\": {\"campo\": ..., \"mensagem\": ...}}`.\n\n"
            "**Exclusao e logica.** `PEDIDO.id_usuario` e FK NOT NULL, entao apagar a "
            "linha seria barrado pela integridade referencial assim que o usuario "
            "tivesse um pedido. O DELETE marca `status_conta = 'excluido'`."
        ),
    },
    "servers": [{"url": "http://127.0.0.1:5000", "description": "Desenvolvimento local"}],
    "tags": [
        {
            "name": "Autenticacao",
            "description": "Login por e-mail ou celular.",
        },
        {
            "name": "Usuarios",
            "description": "Cadastro, consulta, atualizacao e exclusao de usuarios.",
        },
        {"name": "Servico", "description": "Sondas de saude da API."},
    ],
    "components": {
        "schemas": {
            "Usuario": {
                "type": "object",
                "description": (
                    "Representacao publica do usuario. `senha_hash` e `id_social` "
                    "nunca aparecem aqui."
                ),
                "properties": {
                    "id_usuario": {"type": "integer", "example": 1},
                    "nome_completo": {"type": "string", "example": "Maria de Souza"},
                    "email": {
                        "type": "string",
                        "nullable": True,
                        "description": "Nulo quando o cadastro foi feito so por celular.",
                        "example": "maria@exemplo.com",
                    },
                    "celular": {
                        "type": "string",
                        "nullable": True,
                        "description": "So digitos. Nulo quando o cadastro foi so por e-mail.",
                        "example": "11987654321",
                    },
                    "cpf": {"type": "string", "example": "52998224725"},
                    "rg": {"type": "string", "nullable": True},
                    "data_nascimento": {
                        "type": "string", "format": "date", "example": "1998-03-15"
                    },
                    "tipo_usuario": {
                        "type": "string",
                        "enum": ["cliente", "restaurante", "entregador", "admin"],
                    },
                    "status_conta": {
                        "type": "string",
                        "enum": ["pendente", "ativo", "bloqueado", "excluido"],
                        "description": "Nasce 'pendente' ate a validacao do codigo OTP.",
                    },
                    "provedor_social": {
                        "type": "string", "nullable": True, "enum": ["google", "facebook", None]
                    },
                    "data_cadastro": {"type": "string", "format": "date-time"},
                },
            },
            "RespostaUsuario": {
                "type": "object",
                "properties": {"dados": {"$ref": "#/components/schemas/Usuario"}},
                "example": {"dados": _EXEMPLO_USUARIO},
            },
            "Erro": {
                "type": "object",
                "properties": {
                    "erro": {
                        "type": "object",
                        "properties": {
                            "campo": {
                                "type": "string",
                                "description": "Campo que causou a recusa. Ausente em erros gerais.",
                            },
                            "mensagem": {"type": "string"},
                        },
                    }
                },
                "example": {"erro": {"campo": "cpf", "mensagem": "CPF invalido."}},
            },
        }
    },
}


def init_swagger(app):
    """Publica o Swagger UI em /apidocs."""
    return Swagger(app, config=CONFIG, template=TEMPLATE, merge=True)
