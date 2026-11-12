import copy
import re

from app.relative_periods import plain


def monthly_decline_request(messages):
    users = [m for m in messages if m.get("role") == "user"]
    if not users or not isinstance(users[-1].get("content"), str):
        return False
    text = users[-1]["content"]
    if plain(text).strip().rstrip(".!?") == "comparar periodos":
        if (
            len(users) < 2
            or len(messages) < 2
            or messages[-2].get("role") != "assistant"
            or not isinstance(messages[-2].get("content"), str)
            or "Informe se deseja comparar períodos ou analisar um período só."
            not in messages[-2]["content"]
        ):
            return False
        text = users[-2].get("content", "")
    if not isinstance(text, str):
        return False
    text = plain(text)
    return bool(
        re.search(r"\b(?:mes|meses|mensal|mensais)\b", text)
        and re.search(r"\b(?:menor(?:es)?|menos|inferior(?:es)?|abaixo|queda(?:s)?)\b", text)
        and re.search(r"\b(?:compar\w*|ano passado|ano anterior|em relacao)\b", text)
    )


def normalize_monthly_comparison_plan(plan, messages):
    result = copy.deepcopy(plan)
    if not monthly_decline_request(messages):
        return result
    queries = result.get("queries")
    if not isinstance(queries, list) or len(queries) != 1:
        return result
    for query in queries:
        if not isinstance(query, dict):
            continue
        analysis = query.get("analysis")
        if (
            not isinstance(analysis, dict)
            or not isinstance(query.get("period"), dict)
            or not isinstance(query.get("comparison_period"), dict)
            or analysis.get("kind") not in {"comparacao", "tendencia"}
            or analysis.get("group_by") not in {"nenhum", "mes"}
            or analysis.get("detail") not in {"padrao", "quedas"}
        ):
            continue
        query["operation"] = "analysis"
        analysis.update(kind="comparacao", group_by="mes", detail="quedas")
    return result
