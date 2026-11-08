"""Texto gerencial controlado: cálculos e direção exclusivamente das células SQL.

Três formas de apresentação, todas com um único cabeçalho e sem rótulos repetidos:
- total: uma linha ``Rótulo: valor`` por medida;
- lista (ranking, evolução, distribuição): uma linha por item;
- bloco (comparações e análises com várias colunas): item e marcadores.
"""

import calendar
import re
from datetime import date, timedelta

from app.analysis_contract import MONTHS
from app.rendering import (
    COLUMN_LABELS,
    COUNT_NOUNS,
    METRICS,
    PERCENT_COLUMNS,
    InvalidAnswer,
    cell_text,
    percent_text,
    period_text,
)

LABELS = {
    **COLUMN_LABELS,
    "base": "Período base",
    "atual": "Período atual",
    "participacao_variacao": "Contribuição para a variação",
    "posicao": "Posição",
    "desvio": "Desvio de horas",
    "desvio_percentual": "Desvio percentual",
    "saldo": "Saldo de ocorrências",
    "taxa_percentual": "Taxa de resolução",
    "taxa": "Taxa (proporção)",
}
PERCENT = PERCENT_COLUMNS | {"participacao_variacao", "desvio_percentual", "taxa_percentual"}
COUNT_COLUMNS = {"posicao", "quantidade", "chamados_abertos", "chamados_resolvidos", "saldo"}
MEASURE_LABELS = {
    "valor": "Valor",
    "quantidade": "Quantidade",
    "horas_previstas": "Horas previstas",
    "horas_realizadas": "Horas realizadas",
    "chamados_abertos": "Ocorrências abertas",
    "chamados_resolvidos": "Ocorrências resolvidas",
    "taxa_resolucao": "Taxa de resolução",
}
# Colunas de uma consulta total/lista que carregam a medida pedida.
MEASURE_COLUMNS = {"total", "valor", "quantidade", "horas", "taxa"}
LINE_COLUMNS = {"item", "valor", "registros", "participacao", "posicao"}
DIRECTIONS = {
    "aumentou": "📈 Houve aumento em relação ao período base.",
    "diminuiu": "📉 Houve redução em relação ao período base.",
    "ficou_estavel": "O resultado ficou estável em relação ao período base.",
}
TITLES = {
    "comparacao": "Comparativo",
    "tendencia": "Evolução mensal",
    "ranking": "Ranking",
    "segmentacao": "Distribuição",
    "operacional": "Resumo operacional",
    "total": "Resumo",
}
NOT_FOUND = "Não encontrei registros para esses filtros."


def _cell(column, value, context):
    if value is None:
        return "não informado"
    if isinstance(value, bool) or not re.fullmatch(r"-?\d+(?:\.\d+)?", str(value)):
        raise InvalidAnswer("Valor numérico gerencial inválido.")
    formatted = cell_text(value)
    if column in PERCENT:
        return percent_text(value) + "%"
    if column in COUNT_COLUMNS:
        return formatted
    unit = context["unit"]
    if unit == "BRL":
        return "R$ " + formatted
    if unit == "percentual":
        return percent_text(value) + (" p.p." if column == "diferenca" else "%")
    return formatted + (" h" if unit == "horas" else "")


def _amount(column, value, context):
    """Valor de uma linha isolada; contagens ganham o substantivo ("6 pedidos")."""
    text = _cell(column, value, context)
    nouns = COUNT_NOUNS.get(context["metric"])
    if value is not None and nouns and context["unit"] == "quantidade":
        if column in {"valor", "quantidade", "total"}:
            text += " " + nouns[0 if str(value) == "1" else 1]
    return text


def _label(column, context):
    if column in MEASURE_COLUMNS and context.get("measure") in MEASURE_LABELS:
        return MEASURE_LABELS[context["measure"]]
    return LABELS[column]


def header_lines(context: dict) -> tuple[list[str], bool]:
    icon = "🕒" if context["metric"] == "horas" else "📊"
    monthly = context["kind"] == "comparacao" and context.get("group_by") == "mes"
    title = "Comparativo mensal" if monthly else TITLES[context["kind"]]
    lines = [f"{icon} {title} de {METRICS[context['metric']]}"]
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
    return lines, monthly


def grouping_key(context: dict):
    """Identifica contextos com cabeçalho idêntico, variando só a medida."""
    return (
        context.get("metric"),
        context.get("kind"),
        context.get("group_by"),
        json_period(context.get("period")),
        json_period(context.get("comparison_period")),
    )


def json_period(period):
    return (period["start"], period["end"]) if period else None


def measure_subtitle(context: dict) -> str:
    if context.get("unit") == "BRL":
        return "Valor"
    if context.get("unit") == "horas":
        return "Horas"
    return MEASURE_LABELS.get(context.get("measure"), "Quantidade")


def display_item(item, context, monthly: bool) -> str:
    """Nome do item sem o identificador interno que o SQL usa para desempatar."""
    if monthly:
        if not re.fullmatch(r"(?:[1-9]|1[0-2])", str(item)):
            raise InvalidAnswer("Mês gerencial inválido.")
        return MONTHS[int(item) - 1].capitalize()
    text = cell_text(item)
    group = context.get("group_by")
    if group == "mes" and (match := re.fullmatch(r"(\d{4})-(\d{2})-\d{2}", text)):
        year, month = int(match[1]), int(match[2])
        if 1 <= month <= 12:
            return f"{MONTHS[month - 1].capitalize()} de {year}"
    if group in {"cliente", "contrato"} and (match := re.fullmatch(r"(\d+) — (.+)", text)):
        return f"{match[2]} · contrato {match[1]}" if group == "contrato" else match[2]
    return text


def _list_line(record, index, context):
    item = display_item(record["item"], context, False)
    value = _amount("valor", record.get("valor"), context)
    if context["kind"] == "ranking":
        return f"{record.get('posicao', index)}. {item} — {value}"
    line = f"• {item} — {value}"
    if "participacao" in record:
        line += f" ({_cell('participacao', record['participacao'], context)})"
    return line


def _total_lines(record, context):
    lines = []
    for column, value in record.items():
        if column in {"item", "registros", "direcao"}:
            continue
        if column not in LABELS:
            raise InvalidAnswer("Campo gerencial não reconhecido.")
        lines.append(f"{_label(column, context)}: {_amount(column, value, context)}")
    return lines


def _block_lines(record, context, monthly):
    lines = ["", display_item(record["item"], context, monthly)]
    for column, value in record.items():
        if column in {"item", "registros", "direcao"}:
            continue
        if column not in LABELS:
            raise InvalidAnswer("Campo gerencial não reconhecido.")
        lines.append(f"• {_label(column, context)}: {_cell(column, value, context)}")
    return lines


def _render_parts(result: dict, context: dict) -> tuple[list[str], list[str], bool]:
    """Cabeçalho, corpo e se o resultado está vazio (para fundir medidas)."""
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
    header, monthly = header_lines(context)
    records = [dict(zip(columns, row, strict=True)) for row in rows]
    if any(
        "registros" in row and (type(row["registros"]) is not int or row["registros"] < 0)
        for row in records
    ):
        raise InvalidAnswer("Contagem auxiliar inválida.")
    empty = not records or all(r.get("registros") == 0 for r in records)
    if empty and not result.get("truncated"):
        return header, [NOT_FOUND], True
    body: list[str] = []
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
            return header, [message], False
        body.append(
            "Sim. Os meses abaixo apresentaram queda em relação ao mesmo mês do período base."
        )
        if undefined:
            body.append("ℹ️ Há também meses com valores não informados, sem comparação conclusiva.")
        records = declines
    line_form = (
        context["kind"] in {"ranking", "tendencia", "segmentacao"}
        and "item" in columns
        and set(columns) <= LINE_COLUMNS
    )
    if line_form:
        body.append("")
    displayed = 0
    for index, row in enumerate(records, start=1):
        item = row.get("item")
        if line_form:
            block = [_list_line(row, index, context)]
        elif item and item != "Total":
            block = _block_lines(row, context, monthly)
        else:
            block = _total_lines(row, context)
        direction = row.get("direcao")
        if direction in DIRECTIONS:
            block.append(DIRECTIONS[direction])
        if "variacao_percentual" in row and row["variacao_percentual"] is None:
            block.append("ℹ️ Sem base comparável para calcular a variação percentual.")
        if len("\n".join(header + body + block)) > 10000:
            if not displayed:
                raise InvalidAnswer("Registro extenso. Peça um resumo ou refine os filtros.")
            break
        body.extend(block)
        displayed += 1
    if displayed < len(records):
        body.append(
            "ℹ️ Mostrei os primeiros registros do detalhamento. Peça filtros para explorar os demais."
        )
    if result.get("truncated"):
        body.append("ℹ️ Resultado parcial: o limite de linhas foi atingido. Refine os filtros.")
    if context["kind"] == "ranking":
        body.append("ℹ️ Mostrando apenas os principais itens.")
    if context.get("detail") == "fluxos":
        body.append(
            "ℹ️ Emissão e pagamento são fluxos diferentes. A diferença não comprova inadimplência."
        )
    return header, body, False


def render_managerial(result: dict, context: dict) -> str:
    header, body, _ = _render_parts(result, context)
    text = "\n".join(header + body)
    if len(text) > 12000:
        raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")
    return text


def render_managerial_group(items: list[tuple[dict, dict]]) -> str:
    """Mescla resultados com cabeçalho idêntico (mesma métrica, período e tipo),
    variando só a medida, num único bloco em vez de repetir o cabeçalho."""
    if len(items) == 1:
        return render_managerial(*items[0])
    lines: list[str] = []
    for result, context in items:
        header, body, empty = _render_parts(result, context)
        if not lines:
            lines.extend(header)
        if context["kind"] == "total":
            # Totais já trazem o rótulo da medida em cada linha.
            lines.extend([f"{measure_subtitle(context)}: sem registros"] if empty else body)
        else:
            lines.extend(["", f"▸ {measure_subtitle(context)}", *body])
    text = "\n".join(lines)
    if len(text) > 12000:
        raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")
    return text
