from datetime import date, timedelta


_MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def resolver_periodo_relatorio(argumentos, padrao):
    periodo = argumentos.get("periodo") or padrao
    hoje = date.today()

    if periodo == "hoje":
        inicio = fim = hoje
        label = f"Hoje, {hoje:%d/%m/%Y}"
    elif periodo == "semana":
        inicio = hoje - timedelta(days=6)
        fim = hoje
        label = f"Últimos 7 dias · {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"
    elif periodo == "mes":
        inicio = hoje.replace(day=1)
        fim = hoje
        label = f"{_MESES[hoje.month - 1].capitalize()} de {hoje.year}"
    elif periodo == "periodo":
        try:
            inicio = date.fromisoformat(argumentos.get("data_inicio", ""))
            fim = date.fromisoformat(argumentos.get("data_fim", ""))
        except ValueError as erro:
            raise ValueError("Informe as datas inicial e final do período.") from erro
        if inicio > fim:
            raise ValueError("A data inicial não pode ser posterior à data final.")
        label = f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"
    else:
        raise ValueError("Período de relatório inválido.")

    return {
        "periodo": periodo,
        "data_inicio": inicio,
        "data_fim": fim,
        "data_inicio_input": inicio.isoformat(),
        "data_fim_input": fim.isoformat(),
        "periodo_label": label,
    }


def resolver_limite_relatorio(argumentos, opcoes, padrao):
    try:
        limite = int(argumentos.get("limite", padrao))
    except (TypeError, ValueError) as erro:
        raise ValueError("Limite do relatório inválido.") from erro
    if limite not in opcoes:
        raise ValueError("Limite do relatório inválido.")
    return limite
