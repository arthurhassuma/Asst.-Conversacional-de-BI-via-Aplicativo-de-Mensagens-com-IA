import copy

import pytest

from app.managerial_queries import managerial_query
from app.sql_policy import validate_select
from tests.test_analysis_contract import PLAN


def test_custom_filters_never_use_unfiltered_template():
    plan = copy.deepcopy(PLAN)
    plan["analysis"]["custom_filters"] = True
    assert managerial_query(plan) is None


@pytest.mark.parametrize(
    "kind,group,detail,metric,measure",
    [
        ("comparacao", "nenhum", "padrao", "faturamento", "valor"),
        ("comparacao", "segmento", "contribuicao", "faturamento", "valor"),
        ("tendencia", "mes", "padrao", "recebimentos", "valor"),
        ("ranking", "cliente", "padrao", "pedidos", "quantidade"),
        ("segmentacao", "cidade", "padrao", "contratos", "valor"),
        ("operacional", "contrato", "horas", "horas", "horas_realizadas"),
        ("operacional", "nenhum", "chamados", "chamados", "taxa_resolucao"),
        ("operacional", "nenhum", "fluxos", "faturamento", "valor"),
    ],
)
def test_queries_obey_existing_allowlist(kind, group, detail, metric, measure):
    plan = copy.deepcopy(PLAN)
    plan.update(metric=metric, measure=measure)
    plan["analysis"].update(
        kind=kind, group_by=group, detail=detail, limit=5 if kind == "ranking" else None
    )
    if kind != "comparacao":
        plan.pop("comparison_period")
    result = managerial_query(plan)
    assert result is not None
    assert validate_select(result["sql"])
    assert result["context"]["source"] == "controlled_template"


def test_invalid_dimension_or_identifier_is_never_interpolated():
    plan = copy.deepcopy(PLAN)
    plan["analysis"]["group_by"] = "clientes; DELETE FROM clientes"
    assert managerial_query(plan) is None
