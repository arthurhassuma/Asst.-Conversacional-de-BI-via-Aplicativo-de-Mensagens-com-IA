"""SQL gerencial compilado de registros fixos; números calculados no PostgreSQL."""

from datetime import date

from app.analysis_contract import DETAILS, GROUPS, KINDS
from app.query_templates import TOTALS

GROUP_EXPRESSIONS = {
    "nenhum": "'Total'::text",
    "cliente": "c.id::text || ' — ' || c.nome",
    "segmento": "c.segmento",
    "cidade": "c.cidade",
    "contrato": "ct.id::text || ' — ' || c.nome",
}


def _rows(plan, period, group):
    metric, measure = plan["metric"], plan["measure"]
    count = measure == "quantidade"
    opened = resolved = "NULL::numeric"
    if metric in {"faturamento", "recebimentos"}:
        relation = (
            "faturamento f JOIN pedidos p ON p.id=f.pedido_id "
            "JOIN contratos ct ON ct.id=p.contrato_id JOIN clientes c ON c.id=ct.cliente_id"
        )
        field, value = ("f.emissao" if metric == "faturamento" else "f.pagamento"), "f.valor"
        status = "f.status <> 'cancelada'" if metric == "faturamento" else "f.status = 'paga'"
    elif metric == "pedidos":
        relation = "pedidos p JOIN contratos ct ON ct.id=p.contrato_id JOIN clientes c ON c.id=ct.cliente_id"
        field, value, status = (
            "p.data_pedido",
            "1::numeric" if count else "p.valor",
            "p.status <> 'cancelado'",
        )
    elif metric == "contratos":
        relation = "contratos ct JOIN clientes c ON c.id=ct.cliente_id"
        field, value, status = "ct.inicio", "1::numeric" if count else "ct.valor_contratado", "TRUE"
    elif metric == "clientes":
        relation, field, value, status = "clientes c", "c.cadastrado_em", "1::numeric", "TRUE"
    else:
        relation = (
            "indicadores_operacionais i JOIN contratos ct ON ct.id=i.contrato_id "
            "JOIN clientes c ON c.id=ct.cliente_id"
        )
        field, status = "i.competencia", "TRUE"
        value = "i." + measure if measure != "taxa_resolucao" else "i.chamados_resolvidos"
        opened, resolved = "i.chamados_abertos", "i.chamados_resolvidos"
    item = (
        f"date_trunc('month', {field})::date::text" if group == "mes" else GROUP_EXPRESSIONS[group]
    )
    start, end = [date.fromisoformat(period[k]).isoformat() for k in ("start", "end")]
    if start >= end:
        raise ValueError("Período inválido.")
    return (
        f"SELECT {item} AS item, {value} AS valor, {opened} AS abertos, {resolved} AS resolvidos "
        f"FROM {relation} WHERE {status} AND {field} >= DATE '{start}' "
        f"AND {field} < DATE '{end}'"
    )


def _aggregate(plan, relation, group):
    if plan["measure"] == "taxa_resolucao":
        value = "SUM(resolvidos)::numeric * 100 / NULLIF(SUM(abertos), 0)"
    elif plan["measure"] == "quantidade":
        value = "COUNT(*)::numeric"
    else:
        value = "SUM(valor)::numeric"
    item = "'Total'::text AS item" if group == "nenhum" else "item"
    grouping = "" if group == "nenhum" else " GROUP BY item"
    return f"SELECT {item}, {value} AS valor, COUNT(*) AS registros FROM {relation}{grouping}"


def managerial_query(plan: dict) -> dict | None:
    analysis = plan.get("analysis")
    if not isinstance(analysis, dict) or analysis.get("custom_filters") is not False:
        return None
    kind, group, detail = (analysis.get(k) for k in ("kind", "group_by", "detail"))
    if (
        kind not in KINDS
        or group not in GROUPS
        or detail not in DETAILS
        or (plan.get("metric"), plan.get("measure")) not in TOTALS
    ):
        return None
    if plan["metric"] == "clientes" and group == "contrato":
        return None
    if kind == "comparacao" and group == "mes":
        return None  # Alinhamento temporal personalizado segue o executor de SQL.
    if kind == "ranking" and (
        type(analysis.get("limit")) is not int
        or not 1 <= analysis["limit"] <= 100
        or group == "nenhum"
    ):
        return None
    if detail == "contribuicao" and kind != "comparacao":
        return None
    rate = plan["measure"] == "taxa_resolucao"
    if rate and (kind == "segmentacao" or detail == "contribuicao"):
        return None  # Taxas não são aditivas: preservar numeradores/denominadores no SQL livre.
    unit = (
        "BRL"
        if plan["measure"] == "valor"
        else "percentual"
        if plan["measure"] == "taxa_resolucao"
        else "horas"
        if plan["metric"] == "horas"
        else "quantidade"
    )
    context = {
        "source": "controlled_template",
        "kind": kind,
        "group_by": group,
        "detail": detail,
        "unit": unit,
        "metric": plan["metric"],
        "measure": plan["measure"],
        "period": dict(plan["period"]),
        "comparison_period": plan.get("comparison_period"),
        "ranking_limit": analysis.get("limit"),
    }
    rows = _rows(plan, plan["period"], group)
    grouped = _aggregate(plan, "dados", group)
    if kind == "comparacao":
        if not isinstance(plan.get("comparison_period"), dict):
            return None
        other = _rows(plan, plan["comparison_period"], group)
        first, second = (
            _aggregate(plan, "dados_base", group),
            _aggregate(plan, "dados_atual", group),
        )
        contribution = (
            ", (atual-base)*100 / NULLIF(SUM(atual-base) OVER (), 0) AS participacao_variacao"
            if detail == "contribuicao"
            else ""
        )
        base_value = "base.valor" if rate else "CASE WHEN base.registros IS NULL THEN 0 ELSE base.valor END"
        current_value = "atual.valor" if rate else "CASE WHEN atual.registros IS NULL THEN 0 ELSE atual.valor END"
        sql = f"""WITH dados_base AS ({rows}), dados_atual AS ({other}),
            base AS ({first}), atual AS ({second}), comparado AS (
            SELECT COALESCE(base.item, atual.item) AS item,
              {base_value} AS base,
              {current_value} AS atual,
              COALESCE(base.registros,0)+COALESCE(atual.registros,0) AS registros
            FROM base FULL JOIN atual ON base.item=atual.item)
            SELECT item, base, atual, atual-base AS diferenca,
              (atual-base)*100 / NULLIF(base,0) AS variacao_percentual,
              CASE WHEN atual>base THEN 'aumentou' WHEN atual<base THEN 'diminuiu'
                   WHEN atual=base THEN 'ficou_estavel' ELSE 'indefinido' END AS direcao,
              registros {contribution}
            FROM comparado ORDER BY diferenca DESC NULLS LAST, item ASC"""
    elif kind == "operacional" and detail == "horas" and plan["metric"] == "horas":
        # Para horas, uma relação fixa própria conserva ambas as medidas do mesmo registro.
        planned_plan = {**plan, "measure": "horas_previstas"}
        performed_plan = {**plan, "measure": "horas_realizadas"}
        planned = _rows(planned_plan, plan["period"], group)
        performed = _rows(performed_plan, plan["period"], group)
        a = _aggregate(planned_plan, "planejado", group)
        b = _aggregate(performed_plan, "executado", group)
        sql = f"""WITH planejado AS ({planned}), executado AS ({performed}),
          previsto AS ({a}), realizado AS ({b})
          SELECT previsto.item, previsto.valor AS horas_previstas, realizado.valor AS horas_realizadas,
            realizado.valor-previsto.valor AS desvio,
            (realizado.valor-previsto.valor)*100 / NULLIF(previsto.valor,0) AS desvio_percentual,
            previsto.registros AS registros
          FROM previsto JOIN realizado ON previsto.item=realizado.item ORDER BY desvio DESC NULLS LAST, item"""
    elif (
        kind == "operacional"
        and detail == "fluxos"
        and plan["metric"] == "faturamento"
        and group == "nenhum"
    ):
        received_plan = {**plan, "metric": "recebimentos", "measure": "valor"}
        received = _rows(received_plan, plan["period"], group)
        a, b = _aggregate(plan, "emitido", group), _aggregate(received_plan, "recebido", group)
        sql = f"""WITH emitido AS ({rows}), recebido AS ({received}), f AS ({a}), r AS ({b})
          SELECT f.valor AS faturamento, r.valor AS recebimentos, f.valor-r.valor AS diferenca,
            f.registros+r.registros AS registros FROM f CROSS JOIN r"""
    elif kind == "operacional" and detail == "chamados" and plan["metric"] == "chamados":
        item = "'Total'::text AS item" if group == "nenhum" else "item"
        grouping = "" if group == "nenhum" else " GROUP BY item"
        sql = f"""WITH dados AS ({rows}) SELECT {item}, SUM(abertos) AS chamados_abertos,
          SUM(resolvidos) AS chamados_resolvidos, SUM(abertos)-SUM(resolvidos) AS saldo,
          SUM(resolvidos)::numeric*100/NULLIF(SUM(abertos),0) AS taxa_percentual,
          COUNT(*) AS registros FROM dados {grouping} ORDER BY item"""
    elif detail == "padrao" and kind in {"tendencia", "ranking", "segmentacao"}:
        participation = (
            ", valor*100/NULLIF(SUM(valor) OVER (),0) AS participacao"
            if kind == "segmentacao"
            else ""
        )
        position = (
            ", ROW_NUMBER() OVER (ORDER BY valor DESC NULLS LAST, item) AS posicao"
            if kind == "ranking"
            else ""
        )
        order = "item" if kind == "tendencia" else "valor DESC NULLS LAST, item"
        limit = f" LIMIT {analysis['limit']}" if kind == "ranking" else ""
        sql = f"WITH dados AS ({rows}), resumo AS ({grouped}) SELECT item, valor, registros{participation}{position} FROM resumo ORDER BY {order}{limit}"
    else:
        return None
    return {"sql": sql, "context": context}
