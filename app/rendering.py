"""A resposta não incorpora prosa nem números livres produzidos pelo modelo."""

import re
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


def render_answer(payload: dict, results: dict, metric: str) -> str:
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
    if not result["rows"]:
        return "\n".join(lines + ["Nenhum registro foi encontrado para esses filtros."])
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
            )
        )
    if result.get("truncated"):
        lines.append("Resultado parcial: o limite de linhas foi atingido. Refine os filtros.")
    text = "\n".join(lines)
    # Não corte um número no meio para caber no Telegram.
    if len(text) > 12000:
        raise InvalidAnswer("Resultado extenso. Solicite um resumo ou refine os filtros.")
    return text
