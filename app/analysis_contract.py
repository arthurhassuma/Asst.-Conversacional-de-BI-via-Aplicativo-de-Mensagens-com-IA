"""Contratos gerenciais: sem inferir período, filtros ou unidade monetária."""

import re
from datetime import date

MONTHS = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)

KINDS = ("comparacao", "tendencia", "ranking", "segmentacao", "operacional")
GROUPS = ("nenhum", "mes", "cliente", "segmento", "cidade", "contrato")
DETAILS = ("padrao", "contribuicao", "horas", "fluxos", "chamados")
UNSUPPORTED = {
    "custos_ausentes": "ℹ️ Não tenho dados de custos para calcular lucro ou margem. "
    "Posso consultar faturamento, recebimentos ou valor dos pedidos. Qual deseja?",
    "causalidade": "ℹ️ Os registros permitem identificar onde houve variação, mas não comprovar "
    "a causa. Posso detalhar por cliente ou segmento. Qual prefere?",
    "previsao": "ℹ️ Este assistente consulta dados históricos; ainda não tem um modelo "
    "de previsão financeira. Posso mostrar a evolução mensal de um período informado.",
    "fora_escopo": "ℹ️ Posso ajudar com faturamento, recebimentos, pedidos, contratos, clientes, "
    "horas e chamados. Qual indicador e período deseja consultar?",
}


def validate_period(period: dict, messages: list[dict]) -> dict:
    try:
        if not isinstance(period, dict) or set(period) != {"start", "end", "evidence"}:
            raise ValueError
        if not all(
            isinstance(period[k], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", period[k])
            for k in ("start", "end")
        ):
            raise ValueError
        if date.fromisoformat(period["start"]) >= date.fromisoformat(period["end"]):
            raise ValueError
        evidence = period["evidence"]
        if (
            not isinstance(evidence, str)
            or not evidence.strip()
            or not any(
                m.get("role") == "user"
                and isinstance(m.get("content"), str)
                and evidence.casefold() in m["content"].casefold()
                for m in messages
            )
        ):
            raise ValueError
        temporal = re.search(
            r"\b\d{4}\b|(?:mês|ano|semana|trimestre) (?:passado|atual|anterior)|"
            r"(?:este|esta|último|última|últimos|últimas) (?:mês|meses|ano|anos|semana|semanas|trimestre)|"
            r"(?:todo|toda|inteiro) .*(?:histórico|historia)|todo o histórico",
            evidence,
            re.IGNORECASE,
        )
        user_years = set(
            re.findall(
                r"\b(?:19|20)\d{2}\b",
                " ".join(
                    m["content"]
                    for m in messages
                    if m.get("role") == "user" and isinstance(m.get("content"), str)
                ),
            )
        )
        if not temporal and not (
            any(month in evidence.casefold() for month in MONTHS)
            and str(date.fromisoformat(period["start"]).year) in user_years
        ):
            raise ValueError
        years = set(re.findall(r"\b(?:19|20)\d{2}\b", evidence))
        if years and str(date.fromisoformat(period["start"]).year) not in years:
            raise ValueError
        exact_month = re.fullmatch(
            r"(?:em\s+)?(" + "|".join(MONTHS) + r")\s+(?:de\s+)?(\d{4})",
            evidence.strip(),
            re.IGNORECASE,
        )
        if exact_month:
            month, year = MONTHS.index(exact_month[1].casefold()) + 1, int(exact_month[2])
            expected_start = date(year, month, 1)
            expected_end = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
            if (date.fromisoformat(period["start"]), date.fromisoformat(period["end"])) != (
                expected_start,
                expected_end,
            ):
                raise ValueError
    except (KeyError, TypeError, ValueError):
        raise ValueError(
            "Informe os períodos da análise, com mês e ano ou datas explícitas."
        ) from None
    return dict(period)


def validate_analysis(plan: dict, messages: list[dict]) -> dict | None:
    analysis = plan.get("analysis")
    if analysis is None:
        if plan.get("comparison_period") is not None:
            raise ValueError("Informe o tipo de comparação desejado.")
        return None
    if (
        not isinstance(analysis, dict)
        or set(analysis) != {"kind", "group_by", "limit", "detail", "custom_filters"}
        or analysis["kind"] not in KINDS
        or analysis["group_by"] not in GROUPS
        or analysis["detail"] not in DETAILS
        or type(analysis["custom_filters"]) is not bool
        or plan.get("operation") != "analysis"
    ):
        raise ValueError(
            "Não reconheci o tipo de análise. Informe a métrica e o detalhamento desejado."
        )
    limit = analysis["limit"]
    if analysis["kind"] == "ranking":
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Informe um ranking de um a cem itens e a métrica desejada.")
    elif limit is not None:
        raise ValueError("O limite de itens é permitido somente em rankings.")
    period = validate_period(plan.get("period"), messages)
    result = {**analysis, "unequal_periods": False}
    if analysis["kind"] == "comparacao":
        reference = validate_period(plan.get("comparison_period"), messages)

        def duration(p):
            return (date.fromisoformat(p["end"]) - date.fromisoformat(p["start"])).days

        result["unequal_periods"] = duration(period) != duration(reference)
    elif plan.get("comparison_period") is not None:
        raise ValueError("Informe se deseja comparar períodos ou analisar um período só.")
    return result
