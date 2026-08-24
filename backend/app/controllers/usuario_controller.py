"""Controller de usuario - camada C do MVC.

Traduz HTTP em chamadas de servico e servico em HTTP. Nao contem regra de
negocio nem SQL: so le a requisicao, delega e monta a resposta JSON.

O YAML depois do `---` em cada docstring alimenta o Swagger UI em /apidocs.
"""
from flask import current_app, jsonify, request

from app.services import otp_service, usuario_service


def _corpo_json():
    """Le o corpo como JSON sem estourar 415 quando o Content-Type vem errado."""
    return request.get_json(silent=True)


def criar():
    """Cadastra um novo usuario.

    A conta nasce com `status_conta = 'pendente'` e so vira `ativo` apos a
    validacao do codigo OTP (RF01/RF11).

    CPF e celular aceitam mascara - sao normalizados para so digitos antes de
    gravar. O e-mail e gravado em minusculas.

    No cadastro tradicional a senha e obrigatoria e vira hash bcrypt (RF09).
    No cadastro social, envie `provedor_social` e omita `senha`.
    ---
    tags: [Usuarios]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [nome_completo, cpf, data_nascimento]
            properties:
              nome_completo:
                type: string
                minLength: 3
                maxLength: 100
                example: Maria de Souza
              email:
                type: string
                description: Obrigatorio se `celular` nao for informado.
                example: maria@exemplo.com
              celular:
                type: string
                description: DDD + 9 digitos. Aceita mascara.
                example: (11) 98765-4321
              cpf:
                type: string
                description: Validado pelo modulo 11. Aceita mascara.
                example: 529.982.247-25
              rg:
                type: string
                description: Usado apenas para responsavel de restaurante.
              data_nascimento:
                type: string
                format: date
                description: Idade minima de 18 anos.
                example: '1998-03-15'
              senha:
                type: string
                minLength: 8
                description: Obrigatoria, exceto no cadastro social.
                example: senhaSegura123
              tipo_usuario:
                type: string
                enum: [cliente, restaurante, entregador, admin]
                default: cliente
              provedor_social:
                type: string
                enum: [google, facebook]
                description: Presente apenas no login social. Dispensa a senha.
              id_social:
                type: string
                description: ID devolvido pelo provedor OAuth2.
          examples:
            tradicional:
              summary: Cadastro com e-mail e senha
              value:
                nome_completo: Maria de Souza
                email: maria@exemplo.com
                celular: (11) 98765-4321
                cpf: 529.982.247-25
                data_nascimento: '1998-03-15'
                senha: senhaSegura123
            social:
              summary: Cadastro pelo Google, sem senha
              value:
                nome_completo: Joao Lima
                email: joao@exemplo.com
                cpf: '16899535009'
                data_nascimento: '1990-07-02'
                provedor_social: google
                id_social: '108423'
    responses:
      201:
        description: Usuario cadastrado.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/RespostaUsuario'}
      400:
        description: >
          Dado invalido - CPF reprovado no modulo 11, menor de 18 anos,
          e-mail malformado, senha curta ou cadastro sem e-mail e sem celular.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
      409:
        description: E-mail, celular ou CPF ja cadastrado (RF08).
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
            example: {erro: {campo: cpf, mensagem: Ja existe um usuario cadastrado com este cpf.}}
    """
    usuario = usuario_service.criar_usuario(_corpo_json())

    # O controller orquestra os dois servicos do caso de uso: cadastrar e
    # disparar a verificacao. Falha no envio nao desfaz o cadastro - a conta
    # existe, e o usuario pode pedir um reenvio.
    enviado = False
    if usuario.email:
        try:
            _, enviado = otp_service.enviar_codigo(usuario.id_usuario, "cadastro")
        except Exception:
            current_app.logger.exception("Cadastro criado, mas o codigo nao saiu.")

    return jsonify({
        "dados": usuario.to_dict(),
        "verificacao": {"codigo_enviado": enviado},
    }), 201


def listar():
    """Lista usuarios, com paginacao e filtros.

    Contas com `status_conta = 'excluido'` nunca aparecem na listagem.
    ---
    tags: [Usuarios]
    parameters:
      - in: query
        name: pagina
        schema: {type: integer, default: 1, minimum: 1}
      - in: query
        name: por_pagina
        schema: {type: integer, default: 20, minimum: 1, maximum: 100}
      - in: query
        name: tipo_usuario
        schema:
          type: string
          enum: [cliente, restaurante, entregador, admin]
      - in: query
        name: busca
        description: Trecho do nome ou do e-mail.
        schema: {type: string}
        example: maria
    responses:
      200:
        description: Pagina de resultados.
        content:
          application/json:
            schema:
              type: object
              properties:
                dados:
                  type: array
                  items: {$ref: '#/components/schemas/Usuario'}
                paginacao:
                  type: object
                  properties:
                    pagina: {type: integer, example: 1}
                    por_pagina: {type: integer, example: 20}
                    total: {type: integer, example: 1}
                    total_paginas: {type: integer, example: 1}
      400:
        description: Filtro invalido.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
    """
    itens, total, pagina, por_pagina = usuario_service.listar_usuarios(
        pagina=request.args.get("pagina", 1),
        por_pagina=request.args.get("por_pagina", 20),
        tipo_usuario=request.args.get("tipo_usuario"),
        busca=request.args.get("busca"),
    )
    return jsonify({
        "dados": [u.to_dict() for u in itens],
        "paginacao": {
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total": total,
            "total_paginas": (total + por_pagina - 1) // por_pagina,
        },
    }), 200


def buscar(id_usuario):
    """Detalha um usuario pelo id.
    ---
    tags: [Usuarios]
    parameters:
      - in: path
        name: id_usuario
        required: true
        schema: {type: integer}
        example: 1
    responses:
      200:
        description: Usuario encontrado.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/RespostaUsuario'}
      404:
        description: Usuario inexistente ou ja excluido.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
            example: {erro: {mensagem: Usuario 1 nao encontrado.}}
    """
    usuario = usuario_service.buscar_usuario(id_usuario)
    return jsonify({"dados": usuario.to_dict()}), 200


def atualizar(id_usuario):
    """Atualiza dados cadastrais do usuario.

    Atualizacao parcial: so os campos enviados sao alterados.

    **CPF nao e atualizavel** por esta rota - e a chave de negocio da pessoa, e
    permitir a troca abriria caminho para assumir a identidade de outro cadastro.
    `tipo_usuario` e `status_conta` tambem ficam de fora: sao administrativos, e
    o status tem rota propria.

    O usuario nao pode ficar sem e-mail **e** sem celular - ficaria sem como
    receber o codigo OTP.
    ---
    tags: [Usuarios]
    parameters:
      - in: path
        name: id_usuario
        required: true
        schema: {type: integer}
        example: 1
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              nome_completo: {type: string, minLength: 3, maxLength: 100}
              email: {type: string}
              celular: {type: string}
              rg: {type: string}
              data_nascimento: {type: string, format: date}
              senha: {type: string, minLength: 8}
          example:
            nome_completo: Maria Souza Lima
    responses:
      200:
        description: Usuario atualizado.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/RespostaUsuario'}
      400:
        description: >
          Dado invalido, corpo vazio, tentativa de alterar campo nao
          atualizavel (como `cpf`) ou remocao do ultimo contato.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
      404:
        description: Usuario inexistente ou ja excluido.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
      409:
        description: E-mail ou celular ja usado por outro usuario.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
    """
    usuario = usuario_service.atualizar_usuario(id_usuario, _corpo_json())
    return jsonify({"dados": usuario.to_dict()}), 200


def alterar_status(id_usuario):
    """Altera o status da conta.

    Operacao administrativa: ativar apos a validacao do OTP, bloquear por
    excesso de tentativas (RF10/RF11).
    ---
    tags: [Usuarios]
    parameters:
      - in: path
        name: id_usuario
        required: true
        schema: {type: integer}
        example: 1
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [status_conta]
            properties:
              status_conta:
                type: string
                enum: [pendente, ativo, bloqueado, excluido]
          example:
            status_conta: ativo
    responses:
      200:
        description: Status alterado.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/RespostaUsuario'}
      400:
        description: Status fora do dominio aceito.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
      404:
        description: Usuario inexistente ou ja excluido.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
    """
    corpo = _corpo_json() or {}
    usuario = usuario_service.alterar_status(id_usuario, corpo.get("status_conta"))
    return jsonify({"dados": usuario.to_dict()}), 200


def excluir(id_usuario):
    """Exclui o usuario (exclusao logica).

    A linha **nao** e apagada: recebe `status_conta = 'excluido'`. Motivo:
    `PEDIDO.id_usuario` e FK NOT NULL, entao o DELETE fisico seria barrado pela
    integridade referencial assim que o usuario tivesse um pedido - e o
    historico de pedidos seria perdido. Mesmo raciocinio que o projeto ja aplica
    em PRODUTO (`disponivel = false`).

    Depois da exclusao, o usuario some da listagem e o GET por id devolve 404,
    mas a linha continua no banco.
    ---
    tags: [Usuarios]
    parameters:
      - in: path
        name: id_usuario
        required: true
        schema: {type: integer}
        example: 1
    responses:
      200:
        description: Usuario excluido logicamente.
        content:
          application/json:
            schema:
              type: object
              properties:
                mensagem: {type: string}
                observacao: {type: string}
            example:
              mensagem: Usuario excluido.
              observacao: >-
                Exclusao logica: a linha e mantida para preservar o historico
                de pedidos.
      404:
        description: Usuario inexistente ou ja excluido.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
    """
    usuario_service.excluir_usuario(id_usuario)
    return jsonify({
        "mensagem": "Usuario excluido.",
        "observacao": "Exclusao logica: a linha e mantida para preservar o historico de pedidos.",
    }), 200
