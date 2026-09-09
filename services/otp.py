"""
Geração de código de verificação (OTP), compartilhada pelos canais de
e-mail e WhatsApp. Quem envia e confere o código é cada serviço/rota -
este módulo só concentra a regra de geração e o tempo de validade.
"""
import random

CODIGO_VALIDADE_SEGUNDOS = 10 * 60  # 10 minutos


def gerar_codigo():
    """Gera um código numérico de 6 dígitos."""
    return f"{random.randint(0, 999999):06d}"