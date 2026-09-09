"""
Envio de código de verificação via WhatsApp usando automação NÃO OFICIAL
(biblioteca open source whatsapp-web.js), rodando como um microsserviço
Node.js local (pasta whatsapp-service/), controlado pelo número pessoal
do WhatsApp (não é uma Conta Comercial / API oficial da Meta).

ATENÇÃO: essa abordagem não é o método oficialmente suportado pela Meta e
está sujeita aos Termos de Serviço do WhatsApp - o número usado pode ser
banido se o padrão de envio for identificado como automação. Use um
número dedicado para testes sempre que possível.
"""
import os
import requests
from dotenv import load_dotenv
from utils import normalizar_telefone

load_dotenv()

_API_URL = os.getenv("WHATSAPP_LOCAL_API_URL", "http://localhost:3001")


def servico_configurado():
    """Verifica se o microsserviço Node está de pé e com sessão conectada."""
    try:
        resp = requests.get(f"{_API_URL}/status", timeout=3)
        return resp.status_code == 200 and resp.json().get("conectado") is True
    except requests.RequestException:
        return False


def enviar_codigo(telefone, codigo):
    """
    Envia 'codigo' por WhatsApp via o microsserviço local.
    Retorna (sucesso: bool, mensagem_erro: str | None)
    """
    numero = normalizar_telefone(telefone)
    if not numero:
        return False, "Telefone inválido."

    mensagem = (
        f"*Yummy*\nSeu código de verificação é: *{codigo}*\n"
        f"Ele expira em 10 minutos. Não compartilhe com ninguém."
    )

    try:
        resp = requests.post(
            f"{_API_URL}/enviar",
            json={"numero": numero, "mensagem": mensagem},
            timeout=15,
        )
        dados = resp.json()
        if resp.status_code == 200 and dados.get("ok"):
            return True, None
        return False, f"Não foi possível enviar o código pelo WhatsApp: {dados.get('erro', 'erro desconhecido')}"
    except requests.RequestException as e:
        return False, (
            "Serviço local de WhatsApp indisponível. Verifique se o microsserviço "
            f"Node está rodando (whatsapp-service/). Detalhe: {e}"
        )