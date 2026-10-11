"""A resposta não incorpora prosa nem números livres produzidos pelo modelo."""

import re
from datetime import date, timedelta
from decimal import Decimal

METRICS = {
    "faturamento": "faturamento emitido",
    "recebimentos": "recebimentos",
    "pedidos": "pedidos de serviços",
    "contratos": "contratos",
    "clientes": "clientes",
    "horas": "horas de trabalho",
    "chamados": "chamados operacionais",
}


class InvalidAnswer(ValueError):
    pass


def cell_text(value) -> str:
    if value is None:
        return "não informado"
    if isinstance(value, bool):
        return "sim" if value else "não"
    if isinstance(value, (Decimal, int)):
        return str(value).replace(".", ",")
    value = str(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        value = value.replace(".", ",")
    return value.replace("\n", " ").replace("\r", " ")


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
    lines = [f"Consultei {METRICS[metric]} no período informado."]
    if period:
        start = date.fromisoformat(period["start"])
        end = date.fromisoformat(period["end"]) - timedelta(days=1)
        lines.append(f"Período: {start:%d/%m/%Y} a {end:%d/%m/%Y}.")
    measures = {
        "valor": "valor",
        "quantidade": "quantidade",
        "horas_previstas": "horas previstas",
        "horas_realizadas": "horas realizadas",
        "chamados_abertos": "chamados abertos",
        "chamados_resolvidos": "chamados resolvidos",
        "taxa_resolucao": "taxa de resolução",
    }
    if measure in measures:
        lines.append(f"Medida: {measures[measure]}.")
    # SUM sem linhas produz uma linha NULL. Só afirmar ausência quando a
    # consulta traz a contagem de registros; NULL sozinho pode ser dado ausente.
    columns, rows = result["columns"], result["rows"]
    no_records = (
        len(rows) == 1
        and "registros" in columns
        and rows[0][columns.index("registros")] == 0
        and not result.get("truncated")
    )
    if not rows or no_records:
        return "\n".join(lines + ["Nenhum registro foi encontrado para esses filtros."])
    # Frases controladas para um único agregado. O modelo não escreve nem arredonda
    # o valor; detalhes, NULLs e resultados parciais continuam no formato de registros.
    subjects = {
        ("faturamento", "valor"): "faturamento emitido",
        ("recebimentos", "valor"): "recebimentos",
        ("pedidos", "valor"): "valor dos pedidos de serviços",
        ("pedidos", "quantidade"): "quantidade de pedidos de serviços",
        ("contratos", "valor"): "valor contratado",
        ("contratos", "quantidade"): "quantidade de contratos",
        ("clientes", "quantidade"): "quantidade de clientes",
        ("horas", "horas_previstas"): "horas previstas",
        ("horas", "horas_realizadas"): "horas realizadas",
        ("chamados", "chamados_abertos"): "quantidade de chamados abertos",
        ("chamados", "chamados_resolvidos"): "quantidade de chamados resolvidos",
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
            # O alias total também pode vir de AVG ou de uma variação. Não inferir
            # soma, moeda ou porcentagem somente pelo alias ou pelo plano do LLM.
            text = f"No período informado, o resultado para {subject} é {cell_text(value)}."
            if len(text) > 12000:
                raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")
            if period:
                text += f"\nPeríodo: {start:%d/%m/%Y} a {end:%d/%m/%Y}."
            return text
    # Cabeçalhos livres poderiam esconder números gerados (inclusive por extenso).
    # Use rótulos fixos; a lista de colunas segue disponível na evidência interna.
    lines.append("Os campos de cada registro aparecem na ordem da consulta:")
    # Labels sem números só para aliases canônicos do glossário controlado.
    labels = {
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
        "inicio": "Início",
        "fim": "Fim",
        "metrica": "Métrica",
    }
    for row in result["rows"]:
        lines.append(
            " • ".join(
                f"{labels.get(column, 'Campo')}: {cell_text(value)}"
                for column, value in zip(result["columns"], row, strict=True)
                if column != "registros"
            )
        )
    if result.get("truncated"):
        lines.append("Resultado parcial: o limite de linhas foi atingido. Refine os filtros.")
    text = "\n".join(lines)
    # Não corte um número no meio para caber no Telegram.
    if len(text) > 12000:
        raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")
    return text
