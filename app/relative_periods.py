"""Resolve calendário apenas quando há evidência relativa literal do usuário."""

import calendar
import copy
import re
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

MONTHS = (
    "janeiro",
    "fevereiro",
    "marco",
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
CURRENT_YEAR = r"\b(?:(?:este|esse|neste|nesse|deste|desse) ano|ano (?:atual|corrente))\b"
PREVIOUS_YEAR = r"\b(?:ano (?:passado|anterior)|ultimo ano)\b"


def current_date():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()


def plain(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn"
    )


def month_numbers(text):
    return {
        i + 1 for i, month in enumerate(MONTHS) if re.search(r"\b" + month + r"\b", plain(text))
    }


def relative_info(period, messages):
    if not isinstance(period, dict) or not isinstance(period.get("evidence"), str):
        return None
    evidence = period["evidence"]
    source = next(
        (
            m["content"]
            for m in reversed(messages)
            if m.get("role") == "user"
            and isinstance(m.get("content"), str)
            and evidence.strip()
            and evidence.casefold() in m["content"].casefold()
        ),
        None,
    )
    if source is None or re.search(r"\b\d{4}\b", evidence):
        return None
    text = plain(evidence)
    current, previous = bool(re.search(CURRENT_YEAR, text)), bool(re.search(PREVIOUS_YEAR, text))
    if current == previous:
        return None
    months = month_numbers(evidence) or month_numbers(source)
    if len(months) > 1:
        # Intervalos explícitos com vários meses permanecem a cargo do plano validado.
        return None
    return {"offset": 0 if current else -1, "month": next(iter(months), None)}


def comparable_previous_end(today):
    year = today.year - 1
    day = min(today.day, calendar.monthrange(year, today.month)[1])
    return date(year, today.month, day) + timedelta(days=1)


def resolved_period(period, info, today, *, annual_comparison=False):
    year, month = today.year + info["offset"], info["month"]
    if month is not None:
        start = date(year, month, 1)
        end = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
    else:
        start = date(year, 1, 1)
        if info["offset"] == 0:
            end = today + timedelta(days=1)
        elif annual_comparison:
            end = comparable_previous_end(today)
        else:
            end = date(year + 1, 1, 1)
    return {**period, "start": start.isoformat(), "end": end.isoformat()}


def normalize_relative_plan(plan, messages, today=None):
    today = today or current_date()
    result = copy.deepcopy(plan)
    queries = result.get("queries")
    if not isinstance(queries, list):
        return result
    for query in queries:
        if not isinstance(query, dict):
            continue
        fields = ("period", "comparison_period")
        infos = {field: relative_info(query.get(field), messages) for field in fields}
        analysis = query.get("analysis") or {}
        comparison = isinstance(analysis, dict) and analysis.get("kind") == "comparacao"
        pair = (
            comparison and all(infos.values()) and {i["offset"] for i in infos.values()} == {0, -1}
        )
        annual = pair and all(i["month"] is None for i in infos.values())
        for field, info in infos.items():
            if info:
                query[field] = resolved_period(query[field], info, today, annual_comparison=annual)
        # Comparações naturais usam o ano anterior como base. Uma base explicitamente
        # indicada pelo gestor permanece na ordem que ele pediu.
        explicit_base = any(
            m.get("role") == "user"
            and isinstance(m.get("content"), str)
            and re.search(r"\bbase\b", plain(m["content"]))
            for m in messages
        )
        if pair and infos["period"]["offset"] == 0 and not explicit_base:
            query["period"], query["comparison_period"] = (
                query["comparison_period"],
                query["period"],
            )
    return result
