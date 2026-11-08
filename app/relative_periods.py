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
TODAY_WORD = r"\bhoje\b"
YESTERDAY_WORD = r"\bontem\b"
DAY_BEFORE_YESTERDAY_WORD = r"\banteontem\b"
EXPLICIT_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
NAMED_DAY = re.compile(r"\bdia\s+(\d{1,2})\s+de\s+(" + "|".join(MONTHS) + r")(?:\s+de\s+(\d{4}))?\b")


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


RANGE_WORDS = re.compile(r"\b(?:ate|desde|entre)\b")
DAY_WORDS = re.compile(r"\b(?:anteontem|ontem|hoje)\b")


def is_single_day_expression(evidence):
    """Só uma expressão de dia, sem outro limite, mês ou palavra de intervalo.

    "ontem até hoje", "de janeiro até hoje" e "01/02/2026 a 15/02/2026" são intervalos:
    reduzi-los a um dia devolveria um total errado sem avisar o gestor.
    """
    text = plain(evidence)
    expressions = (
        len(DAY_WORDS.findall(text))
        + len(EXPLICIT_DATE.findall(evidence))
        + len(NAMED_DAY.findall(text))
    )
    if expressions != 1 or RANGE_WORDS.search(text):
        return False
    named = NAMED_DAY.search(text)
    # O mês de "dia 20 de janeiro" pertence à própria expressão; qualquer outro, não.
    return len(month_numbers(text)) <= (1 if named else 0)


def exact_day(evidence, today):
    """Resolve hoje/ontem/anteontem e datas de um único dia, explícitas ou nomeadas."""
    if not is_single_day_expression(evidence):
        return None
    text = plain(evidence)
    if re.search(DAY_BEFORE_YESTERDAY_WORD, text):
        return today - timedelta(days=2)
    if re.search(YESTERDAY_WORD, text):
        return today - timedelta(days=1)
    if re.search(TODAY_WORD, text):
        return today
    match = EXPLICIT_DATE.search(evidence)
    if match:
        day, month, year = (int(group) for group in match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None
    match = NAMED_DAY.search(text)
    if match:
        day, month = int(match.group(1)), MONTHS.index(match.group(2)) + 1
        year_text = match.group(3)
        if year_text:
            year = int(year_text)
        else:
            current = bool(re.search(CURRENT_YEAR, text))
            previous = bool(re.search(PREVIOUS_YEAR, text))
            if current == previous:
                return None
            year = today.year + (0 if current else -1)
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def relative_info(period, messages, today):
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
    if source is None:
        return None
    day = exact_day(evidence, today)
    if day is not None:
        return {"exact": day}
    if re.search(r"\b\d{4}\b", evidence):
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


def single_month(period):
    """Mês de um período que cobre exatamente um mês de calendário, senão None."""
    try:
        start, end = date.fromisoformat(period["start"]), date.fromisoformat(period["end"])
    except (KeyError, TypeError, ValueError):
        return None
    following = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    return start.month if start.day == 1 and end == following else None


def comparable_previous_end(today):
    year = today.year - 1
    day = min(today.day, calendar.monthrange(year, today.month)[1])
    return date(year, today.month, day) + timedelta(days=1)


def resolved_period(period, info, today, *, annual_comparison=False):
    if "exact" in info:
        start = info["exact"]
        return {**period, "start": start.isoformat(), "end": (start + timedelta(days=1)).isoformat()}
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
        infos = {field: relative_info(query.get(field), messages, today) for field in fields}
        exact = any("exact" in (info or {}) for info in infos.values())
        analysis = query.get("analysis") or {}
        comparison = isinstance(analysis, dict) and analysis.get("kind") == "comparacao"
        if comparison and not exact:
            # "Compara com o ano passado" depois de fixar um mês: o mês está no outro
            # período do plano ("agosto de 2026"), não na evidência relativa.
            for field, other in (("period", "comparison_period"), ("comparison_period", "period")):
                info = infos[field]
                month = single_month(query.get(other) or {})
                if info and info["month"] is None and month and not infos[other]:
                    infos[field] = {**info, "month": month}
        pair = (
            comparison
            and not exact
            and all(infos.values())
            and {i["offset"] for i in infos.values()} == {0, -1}
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
