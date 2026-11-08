"""Totais simples definidos pelo plano, sem SQL livre gerado pelo modelo."""

from datetime import date

# Identificadores e expressões são fixos; só entram datas ISO validadas.
TOTALS = {
    ("faturamento", "valor"): (
        "faturamento",
        "emissao",
        "SUM(valor)",
        "total",
        "status <> 'cancelada'",
    ),
    ("recebimentos", "valor"): (
        "faturamento",
        "pagamento",
        "SUM(valor)",
        "total",
        "status = 'paga'",
    ),
    ("pedidos", "valor"): (
        "pedidos",
        "data_pedido",
        "SUM(valor)",
        "total",
        "status <> 'cancelado'",
    ),
    ("pedidos", "quantidade"): (
        "pedidos",
        "data_pedido",
        "COUNT(*)",
        "quantidade",
        "status <> 'cancelado'",
    ),
    ("contratos", "valor"): ("contratos", "inicio", "SUM(valor_contratado)", "total", "TRUE"),
    ("contratos", "quantidade"): ("contratos", "inicio", "COUNT(*)", "quantidade", "TRUE"),
    ("clientes", "quantidade"): ("clientes", "cadastrado_em", "COUNT(*)", "quantidade", "TRUE"),
    ("horas", "horas_previstas"): (
        "indicadores_operacionais",
        "competencia",
        "SUM(horas_previstas)",
        "horas",
        "TRUE",
    ),
    ("horas", "horas_realizadas"): (
        "indicadores_operacionais",
        "competencia",
        "SUM(horas_realizadas)",
        "horas",
        "TRUE",
    ),
    ("chamados", "chamados_abertos"): (
        "indicadores_operacionais",
        "competencia",
        "SUM(chamados_abertos)",
        "quantidade",
        "TRUE",
    ),
    ("chamados", "chamados_resolvidos"): (
        "indicadores_operacionais",
        "competencia",
        "SUM(chamados_resolvidos)",
        "quantidade",
        "TRUE",
    ),
    ("chamados", "taxa_resolucao"): (
        "indicadores_operacionais",
        "competencia",
        # Em pontos percentuais, como o template gerencial: o texto mostra "85,71%".
        "SUM(chamados_resolvidos)::numeric * 100 / NULLIF(SUM(chamados_abertos), 0)",
        "taxa",
        "TRUE",
    ),
}


def total_query(plan: dict) -> str:
    table, field, aggregate, label, status = TOTALS[(plan["metric"], plan["measure"])]
    start = date.fromisoformat(plan["period"]["start"]).isoformat()
    end = date.fromisoformat(plan["period"]["end"]).isoformat()
    if start >= end:
        raise ValueError("Período inválido.")
    return (
        f"SELECT {aggregate} AS {label}, COUNT(*) AS registros FROM {table} "
        f"WHERE {field} >= DATE '{start}' AND {field} < DATE '{end}' AND {status}"
    )
