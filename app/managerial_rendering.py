"""Texto gerencial controlado: cálculos e direção exclusivamente das células SQL."""

import calendar
import re
from datetime import date, timedelta

from app.analysis_contract import MONTHS
from app.rendering import METRICS, InvalidAnswer, cell_text, percent_text

LABELS = {
    "base": "Período base",
    "atual": "Período atual",
    "diferenca": "Diferença",
    "variacao_percentual": "Variação percentual",
    "participacao_variacao": "Contribuição para a variação",
    "valor": "Valor",
    "participacao": "Participação",
    "posicao": "Posição",
    "horas_previstas": "Horas previstas",
    "horas_realizadas": "Horas realizadas",
    "desvio": "Desvio de horas",
    "desvio_percentual": "Desvio percentual",
    "chamados_abertos": "Chamados abertos",
    "chamados_resolvidos": "Chamados resolvidos",
    "saldo": "Saldo de chamados",
    "taxa_percentual": "Taxa de resolução",
    "faturamento": "Faturamento emitido",
    "recebimentos": "Recebimentos",
    "total": "Total",
    "quantidade": "Quantidade",
    "horas": "Horas",
    "taxa": "Taxa (proporção)",
}
PERCENT = {
    "variacao_percentual",
    "participacao_variacao",
    "participacao",
    "desvio_percentual",
    "taxa_percentual",
}
DIRECTIONS = {
    "aumentou": "📈 Houve aumento em relação ao período base.",
    "diminuiu": "📉 Houve redução em relação ao período base.",
    "ficou_estavel": "O resultado ficou estável em relação ao período base.",
}


def period_text(period):
    start = date.fromisoformat(period["start"])
    end = date.fromisoformat(period["end"]) - timedelta(days=1)
    return f"{start:%d/%m/%Y} a {end:%d/%m/%Y}"


def _cell(column, value, context):
    if value is None:
        return "não informado"
    if isinstance(value, bool) or not re.fullmatch(r"-?\d+(?:\.\d+)?", str(value)):
        raise InvalidAnswer("Valor numérico gerencial inválido.")
    formatted = cell_text(value)
    if column in PERCENT:
        return percent_text(value) + "%"
    if column in {"posicao", "quantidade", "chamados_abertos", "chamados_resolvidos", "saldo"}:
        return formatted
    unit = context["unit"]
    if unit == "BRL":
        return "R$ " + formatted
    if unit == "percentual":
        return percent_text(value) + (" p.p." if column == "diferenca" else "%")
    return formatted + (" h" if unit == "horas" else "")


def render_managerial(result: dict, context: dict) -> str:
    if (
        context.get("source") != "controlled_template"
        or context.get("metric") not in METRICS
        or context.get("unit") not in {"BRL", "percentual", "horas", "quantidade"}
        or "error" in result
    ):
        raise InvalidAnswer("Contexto gerencial não validado.")
    columns, rows = result["columns"], result["rows"]
    if len(set(columns)) != len(columns) or any(len(row) != len(columns) for row in rows):
        raise InvalidAnswer("Formato do resultado gerencial inválido.")
    titles = {
        "comparacao": "Comparativo",
        "tendencia": "Evolução mensal",
        "ranking": "Ranking",
        "segmentacao": "Distribuição",
        "operacional": "Resumo operacional",
        "total": "Resumo",
    }
    icon = "🕒" if context["metric"] == "horas" else "📊"
    lines = [f"{icon} {titles[context['kind']]} de {METRICS[context['metric']]}"]
    monthly = context["kind"] == "comparacao" and context.get("group_by") == "mes"
    if monthly:
        lines[0] = f"{icon} Comparativo mensal de {METRICS[context['metric']]}"
    lines.append("Período: " + period_text(context["period"]))
    if context.get("comparison_period"):
        lines.append("Comparado com: " + period_text(context["comparison_period"]))
        lengths = [
            (date.fromisoformat(p["end"]) - date.fromisoformat(p["start"])).days
            for p in (context["period"], context["comparison_period"])
        ]
        if lengths[0] != lengths[1]:
            lines.append(
                "ℹ️ Os intervalos têm durações diferentes; interprete os totais com esse cuidado."
            )
        if monthly:
            last_day = date.fromisoformat(context["comparison_period"]["end"]) - timedelta(days=1)
            if last_day.day < calendar.monthrange(last_day.year, last_day.month)[1]:
                lines.append("ℹ️ O último mês está parcial nos intervalos comparados.")
    records = [dict(zip(columns, row, strict=True)) for row in rows]
    if any(
        "registros" in row and (type(row["registros"]) is not int or row["registros"] < 0)
        for row in records
    ):
        raise InvalidAnswer("Contagem auxiliar inválida.")
    empty = not records or all(r.get("registros") == 0 for r in records)
    if empty and not result.get("truncated"):
        return "\n".join(lines + ["Não encontrei registros para esses filtros."])
    if monthly and context.get("detail") == "quedas":
        declines = [row for row in records if row.get("direcao") == "diminuiu"]
        undefined = any(row.get("direcao") == "indefinido" for row in records)
        if not declines:
            if result.get("truncated"):
                message = (
                    "Não encontrei quedas nas linhas disponíveis. "
                    "ℹ️ Resultado parcial: refine os filtros para concluir a comparação."
                )
            elif undefined:
                message = (
                    "Não encontrei queda nos meses com valores comparáveis. "
                    "Há meses com valores não informados; não é possível concluir sobre eles."
                )
            else:
                message = (
                    "Não. Nenhum dos meses com registros nos intervalos consultados apresentou "
                    "resultado menor que o do mesmo mês no período base."
                )
            return "\n".join(lines + [message])
        lines.append(
            "Sim. Os meses abaixo apresentaram queda em relação ao mesmo mês do período base."
        )
        if undefined:
            lines.append("ℹ️ Há também meses com valores não informados, sem comparação conclusiva.")
        records = declines
    displayed = 0
    for row in records:
        block_start = len(lines)
        item = row.get("item")
        if item and item != "Total":
            if monthly:
                if not re.fullmatch(r"(?:[1-9]|1[0-2])", str(item)):
                    raise InvalidAnswer("Mês gerencial inválido.")
                item = MONTHS[int(item) - 1].capitalize()
            lines.extend(["", cell_text(item)])
        else:
            lines.append("")
        for column, value in row.items():
            if column in {"item", "registros", "direcao"}:
                continue
            if column not in LABELS:
                raise InvalidAnswer("Campo gerencial não reconhecido.")
            label = LABELS[column]
            if column == "valor" and context["unit"] == "quantidade":
                label = "Quantidade"
            lines.append(f"• {label}: {_cell(column, value, context)}")
        direction = row.get("direcao")
        if direction in DIRECTIONS:
            lines.append(DIRECTIONS[direction])
        if "variacao_percentual" in row and row["variacao_percentual"] is None:
            lines.append("ℹ️ Sem base comparável para calcular a variação percentual.")
        if len("\n".join(lines)) > 10000:
            del lines[block_start:]
            if not displayed:
                raise InvalidAnswer("Registro extenso. Peça um resumo ou refine os filtros.")
            break
        displayed += 1
    if displayed < len(records):
        lines.append(
            "ℹ️ Mostrei os primeiros registros do detalhamento. Peça filtros para explorar os demais."
        )
    if result.get("truncated"):
        lines.append("ℹ️ Resultado parcial: o limite de linhas foi atingido. Refine os filtros.")
    if context["kind"] == "ranking":
        lines.append("ℹ️ Ranking limitado aos principais itens; empates têm ordenação estável.")
    if context.get("detail") == "fluxos":
        lines.append(
            "ℹ️ Emissão e pagamento são fluxos diferentes. A diferença não comprova inadimplência."
        )
    text = "\n".join(lines)
    if len(text) > 12000:
        raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")
    return text
