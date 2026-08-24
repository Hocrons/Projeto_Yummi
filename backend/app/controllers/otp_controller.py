"""Controller do codigo de verificacao - camada C do MVC."""
from flask import jsonify, request

from app.services import otp_service


def enviar():
    """Envia (ou reenvia) o codigo de verificacao por e-mail.

    Gera um codigo de 6 digitos valido por 5 minutos e manda para o e-mail do
    usuario. Novo pedido so e aceito 60 segundos apos o anterior (RF04).

    Sem SMTP configurado no `.env`, o codigo aparece no log do backend em vez
    de ser enviado - a resposta avisa isso em `enviado_por_email`.
    ---
    tags: [Verificacao]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [id_usuario]
            properties:
              id_usuario: {type: integer, example: 1}
              finalidade:
                type: string
                enum: [cadastro, login]
                default: cadastro
          example: {id_usuario: 1}
    responses:
      200:
        description: Codigo gerado.
        content:
          application/json:
            schema:
              type: object
              properties:
                dados:
                  type: object
                  properties:
                    id_usuario: {type: integer}
                    expira_em: {type: string, format: date-time}
                    enviado_por_email:
                      type: boolean
                      description: false = o codigo saiu no log, nao no e-mail.
      400:
        description: Reenvio pedido antes dos 60 segundos, ou usuario sem e-mail.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
      404:
        description: Usuario inexistente ou excluido.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
    """
    corpo = request.get_json(silent=True) or {}
    codigo, enviado = otp_service.enviar_codigo(
        corpo.get("id_usuario"), corpo.get("finalidade") or "cadastro"
    )
    return jsonify({
        "dados": {
            "id_usuario": codigo.id_usuario,
            "expira_em": codigo.expira_em.isoformat(),
            "enviado_por_email": enviado,
        }
    }), 200


def validar():
    """Valida o codigo e ativa a conta.

    Acertando, a conta sai de `pendente` para `ativo` e o login passa a
    funcionar (RF11). Cada erro consome uma das 5 tentativas; esgotadas, o
    codigo morre e e preciso pedir outro (RF10).
    ---
    tags: [Verificacao]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [id_usuario, codigo]
            properties:
              id_usuario: {type: integer, example: 1}
              codigo: {type: string, example: '123456'}
              finalidade:
                type: string
                enum: [cadastro, login]
                default: cadastro
          example: {id_usuario: 1, codigo: '123456'}
    responses:
      200:
        description: Codigo aceito. A conta foi ativada.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/RespostaUsuario'}
      400:
        description: >
          Codigo incorreto, expirado, ja usado, ou tentativas esgotadas.
          A mensagem diz quantas tentativas restam.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
      404:
        description: Usuario inexistente ou excluido.
        content:
          application/json:
            schema: {$ref: '#/components/schemas/Erro'}
    """
    corpo = request.get_json(silent=True) or {}
    usuario = otp_service.validar_codigo(
        corpo.get("id_usuario"), corpo.get("codigo"), corpo.get("finalidade") or "cadastro"
    )
    return jsonify({"dados": usuario.to_dict()}), 200
