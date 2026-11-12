import re
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, localcontext

METRICS = {
    "faturamento": "faturamento emitido",
    "recebimentos": "recebimentos",
    "pedidos": "pedidos de venda",
    "contratos": "contratos de fornecimento",
    "clientes": "clientes",
    "horas": "horas de atendimento",
    "chamados": "ocorrências de pós-venda",
}

COLUMN_LABELS = {
    "total": "Total",
    "nome": "Nome",
    "cliente": "Cliente",
    "valor": "Valor",
    "quantidade": "Quantidade",
    "mes": "Mês",
    "periodo": "Período",
    "horas": "Horas",
    "taxa": "Taxa",
    "status": "Situação",
    "uf": "UF",
    "modalidade": "Modalidade",
    "segmento": "Segmento",
    "cidade": "Cidade",
    "inicio": "Início",
    "fim": "Fim",
    "metrica": "Métrica",
    "media": "Média",
    "ticket_medio": "Ticket médio",
    "base": "Base",
    "atual": "Atual",
    "diferenca": "Diferença",
    "variacao_percentual": "Variação percentual",
    "participacao": "Participação",
    "faturamento": "Faturamento emitido",
    "recebimentos": "Recebimentos",
    "horas_previstas": "Horas previstas",
    "horas_realizadas": "Horas realizadas",
    "chamados_abertos": "Ocorrências abertas",
    "chamados_resolvidos": "Ocorrências resolvidas",
}
PERCENT_COLUMNS = {"variacao_percentual", "participacao"}

COUNT_NOUNS = {
    "pedidos": ("pedido", "pedidos"),
    "contratos": ("contrato", "contratos"),
    "clientes": ("cliente", "clientes"),
    "chamados": ("ocorrência", "ocorrências"),
}


class InvalidAnswer(ValueError):
    pass


def percent_text(value) -> str:
    if value is None:
        return "não informado"
    if isinstance(value, bool) or not re.fullmatch(r"-?\d+(?:\.\d+)?", str(value)):
        raise InvalidAnswer("Percentual inválido.")
    with localcontext() as context:
        context.prec = max(28, len(str(value)) + 4)
        rounded = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = abs(rounded)
    return cell_text(format(rounded, ".2f"))


def cell_text(value) -> str:
    if value is None:
        return "não informado"
    if isinstance(value, bool):
        return "sim" if value else "não"
    value = str(value)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        sign = "-" if value.startswith("-") else ""
        whole, dot, fraction = value.lstrip("-").partition(".")
        groups = []
        while whole:
            groups.insert(0, whole[-3:])
            whole = whole[:-3]
        return sign + ".".join(groups) + ("," + fraction if dot else "")
    return value.replace("\n", " ").replace("\r", " ")


def period_text(period: dict) -> str:
    start = date.fromisoformat(period["start"])
    end = date.fromisoformat(period["end"]) - timedelta(days=1)
    if start == end:
        return f"{start:%d/%m/%Y}"
    return f"{start:%d/%m/%Y} a {end:%d/%m/%Y}"


def render_answer(
    payload: dict,
    results: dict,
    metric: str,
    period: dict | None = None,
    measure: str | None = None,
) -> str:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"kind", "result_id"}
        or payload["kind"] != "answer"
        or not isinstance(payload["result_id"], str)
        or payload["result_id"] not in results
        or metric not in METRICS
    ):
        raise InvalidAnswer("A resposta não referencia um resultado válido.")
    result = results[payload["result_id"]]
    lines = [f"📊 Resultado de {METRICS[metric]}"]
    if period:
        lines.append(f"Período: {period_text(period)}")
    measures = {
        "valor": "valor",
        "quantidade": "quantidade",
        "horas_previstas": "horas previstas",
        "horas_realizadas": "horas realizadas",
        "chamados_abertos": "ocorrências abertas",
        "chamados_resolvidos": "ocorrências resolvidas",
        "taxa_resolucao": "taxa de resolução",
    }
    columns, rows = result["columns"], result["rows"]
    no_records = (
        len(rows) == 1
        and "registros" in columns
        and rows[0][columns.index("registros")] == 0
        and not result.get("truncated")
    )
    if not rows or no_records:
        return "\n".join(lines + ["Não encontrei registros para esses filtros."])
    subjects = {
        ("faturamento", "valor"): "faturamento emitido",
        ("recebimentos", "valor"): "recebimentos",
        ("pedidos", "valor"): "valor dos pedidos de venda",
        ("pedidos", "quantidade"): "quantidade de pedidos de venda",
        ("contratos", "valor"): "valor contratado",
        ("contratos", "quantidade"): "quantidade de contratos de fornecimento",
        ("clientes", "quantidade"): "quantidade de clientes",
        ("horas", "horas_previstas"): "horas previstas",
        ("horas", "horas_realizadas"): "horas realizadas",
        ("chamados", "chamados_abertos"): "quantidade de ocorrências abertas",
        ("chamados", "chamados_resolvidos"): "quantidade de ocorrências resolvidas",
    }
    subject = subjects.get((metric, measure))
    if (
        subject
        and not result.get("truncated")
        and len(result["rows"]) == 1
        and len(result["rows"][0]) == 1
        and result["columns"] == ["total"]
    ):
        value = result["rows"][0][0]
        if re.fullmatch(r"-?\d+(?:\.\d+)?", str(value)):
            text = f"📊 Resultado para {subject}: {cell_text(value)}."
            if period:
                text += f"\nPeríodo: {period_text(period)}"
            return text
    labels = COLUMN_LABELS
    visible = [column for column in columns if column != "registros"]
    if len(rows) == 1 and len(visible) == 1 and not result.get("truncated"):
        column = visible[0]
        value = rows[0][columns.index(column)]
        label = labels.get(column, "Campo")
        if measure in measures and column in {"total", "valor", "quantidade", "horas", "taxa"}:
            label = measures[measure].capitalize()
        shown = (
            percent_text(value) + ("%" if value is not None else "")
            if column in PERCENT_COLUMNS
            else cell_text(value)
        )
        return "\n".join(lines + [f"{label}: {shown}"])
    if measure in measures:
        lines.append(f"Medida: {measures[measure]}")
    for row in result["rows"]:
        lines.append(
            "• "
            + " · ".join(
                f"{labels.get(column, 'Campo')}: "
                + (
                    percent_text(value) + ("%" if value is not None else "")
                    if column in PERCENT_COLUMNS
                    else cell_text(value)
                )
                for column, value in zip(result["columns"], row, strict=True)
                if column != "registros"
            )
        )
    if result.get("truncated"):
        lines.append("ℹ️ Resultado parcial: o limite de linhas foi atingido. Refine os filtros.")
    text = "\n".join(lines)
    if len(text) > 12000:
        raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")
    return text
