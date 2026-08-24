"""Controller de autenticacao - camada C do MVC.

Nao decide nada sobre credencial: delega ao auth_service e traduz o resultado
em resposta HTTP.
"""
from flask import jsonify, request

from app.services import auth_service


def login():
    """Autentica o usuario por e-mail ou celular.

    Envie **e-mail ou celular**, junto com a senha.

    Senha errada e usuario inexistente devolvem a **mesma** resposta 401, de
    proposito: diferenciar as duas contaria a quem esta tentando invadir se
    aquele e-mail existe na base.

    Conta correta mas nao liberada devolve **403** com o motivo - pendente de
    verificacao (RF11) ou bloqueada (RF10). Aqui a mensagem e especifica porque
    quem chegou ate este ponto ja provou saber a senha.

    Conta criada por Google/Facebook nao tem senha local, entao o login
    tradicional nela falha como credencial invalida (RF05).
    ---
    tags: [Autenticacao]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [senha]
            properties:
              email:
                type: string
                description: Informe este **ou** `celular`.
                example: maria@exemplo.com
              celular:
                type: string
                description: Informe este **ou** `email`. Aceita mascara.
                example: (11) 98765-4321
              senha:
                type: string
                example: senhaSegura123
          examples:
            por_email:
              summary: Entrar com e-mail
              value: {email: maria@exemplo.com, senha: senhaSegura123}
            por_celular:
              summary: Entrar com celular
              value: {celular: (11) 98765-4321, senha: senhaSegura123}
    responses:
      200:
        description: Autenticado. Devolve os dados do usuario.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/RespostaUsuario'}
      400:
        description: Faltou a senha, ou nao veio nem e-mail nem celular.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
      401:
        description: E-mail/celular ou senha incorretos.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
            example: {erro: {mensagem: E-mail ou senha incorretos.}}
      403:
        description: >
          Credencial correta, mas a conta esta pendente de verificacao ou
          bloqueada. O campo `status_conta` diz qual dos dois.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
    """
    usuario = auth_service.autenticar(request.get_json(silent=True))
    return jsonify({"dados": usuario.to_dict()}), 200
