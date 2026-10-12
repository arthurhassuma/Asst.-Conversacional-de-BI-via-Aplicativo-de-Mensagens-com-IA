import copy
import os
from decimal import Decimal

import pytest

from app.config import Settings
from app.database_tools import DatabaseTools
from app.managerial_queries import managerial_query
from tests.test_analysis_contract import PLAN


@pytest.fixture
def database():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Requer PostgreSQL real.")
    return DatabaseTools(Settings(_env_file=None, database_url=dsn))


@pytest.mark.integration
def test_comparison_matches_independent_totals(database):
    compiled = managerial_query(PLAN)
    result = database.execute_sql(compiled["sql"])
    assert "error" not in result and not result["truncated"]
    row = dict(zip(result["columns"], result["rows"][0], strict=True))
    expected = []
    for year in (2025, 2026):
        reference = database.execute_sql(
            f"SELECT SUM(valor) AS total FROM faturamento "
            f"WHERE status <> 'cancelada' AND emissao >= DATE '{year}-08-01' "
            f"AND emissao < DATE '{year}-09-01'"
        )
        expected.append(Decimal(reference["rows"][0][0]))
    assert Decimal(row["base"]) == expected[0]
    assert Decimal(row["atual"]) == expected[1]
    assert Decimal(row["diferenca"]) == expected[1] - expected[0]


@pytest.mark.integration
def test_missing_calls_preserve_undefined_rate(database, monkeypatch):
    import app.managerial_queries as module
    def rows(plan, period, group):
        values = "('Saiu',10,8)" if period["start"].startswith("2025") else "('Entrou',10,8)"
        return f"SELECT item, resolvidos::numeric AS valor, abertos, resolvidos FROM (VALUES {values}) AS v(item,abertos,resolvidos)"
    monkeypatch.setattr(module, "_rows", rows)
    plan = copy.deepcopy(PLAN)
    plan.update(metric="chamados", measure="taxa_resolucao")
    plan["analysis"].update(group_by="cliente")
    result = database.execute_sql(module.managerial_query(plan)["sql"])
    assert "error" not in result
    data = {r[0]: dict(zip(result["columns"], r, strict=True)) for r in result["rows"]}
    assert data["Entrou"]["base"] is None and data["Saiu"]["atual"] is None
    assert all(r["diferenca"] is None and r["direcao"] == "indefinido" for r in data.values())


@pytest.mark.integration
def test_contributions_sum_to_independent_difference(database):
    plan = copy.deepcopy(PLAN)
    plan["analysis"].update(group_by="segmento", detail="contribuicao")
    result = database.execute_sql(managerial_query(plan)["sql"])
    global_result = database.execute_sql(managerial_query(PLAN)["sql"])
    assert "error" not in result and not result["truncated"]
    index = result["columns"].index("diferenca")
    total = sum(Decimal(r[index]) for r in result["rows"])
    expected = global_result["rows"][0][global_result["columns"].index("diferenca")]
    assert total == Decimal(expected)


@pytest.mark.integration
def test_zero_reference_yields_undefined_percentage(database):
    plan = copy.deepcopy(PLAN)
    plan["metric"], plan["measure"] = "pedidos", "quantidade"
    plan["period"].update(start="2027-01-01", end="2027-02-01")
    result = database.execute_sql(managerial_query(plan)["sql"])
    assert "error" not in result
    row = dict(zip(result["columns"], result["rows"][0], strict=True))
    assert Decimal(row["base"]) == 0 and row["variacao_percentual"] is None


@pytest.mark.integration
def test_entry_exit_and_existing_null_are_not_conflated(database, monkeypatch):
    import app.managerial_queries as module

    def rows(plan, period, group):
        values = (
            "('Mantido',10),('Saiu',20),('Valor ausente',NULL)"
            if period["start"].startswith("2025")
            else "('Mantido',30),('Entrou',40),('Valor ausente',NULL)"
        )
        return f"SELECT item, valor::numeric AS valor FROM (VALUES {values}) AS v(item,valor)"

    monkeypatch.setattr(module, "_rows", rows)
    plan = copy.deepcopy(PLAN)
    plan["analysis"].update(group_by="cliente", detail="contribuicao")
    result = database.execute_sql(module.managerial_query(plan)["sql"])
    assert "error" not in result
    data = {r[0]: dict(zip(result["columns"], r, strict=True)) for r in result["rows"]}
    assert Decimal(data["Entrou"]["base"]) == 0
    assert Decimal(data["Saiu"]["atual"]) == 0
    assert data["Valor ausente"]["base"] is None
    assert data["Valor ausente"]["atual"] is None


@pytest.mark.integration
def test_no_calls_has_undefined_resolution_and_ties_have_stable_ranks(database, monkeypatch):
    import app.managerial_queries as module

    monkeypatch.setattr(
        module,
        "_rows",
        lambda *args: (
            "SELECT item, valor::numeric AS valor, 0 AS abertos, 0 AS resolvidos "
            "FROM (VALUES ('B',10),('A',10)) AS v(item,valor)"
        ),
    )
    plan = copy.deepcopy(PLAN)
    plan.pop("comparison_period")
    plan.update(metric="chamados", measure="taxa_resolucao")
    plan["analysis"].update(kind="operacional", group_by="nenhum", detail="chamados")
    result = database.execute_sql(module.managerial_query(plan)["sql"])
    assert "error" not in result
    assert result["rows"][0][result["columns"].index("taxa_percentual")] is None
    plan.update(metric="pedidos", measure="valor")
    plan["analysis"].update(kind="ranking", group_by="cliente", detail="padrao", limit=2)
    result = database.execute_sql(module.managerial_query(plan)["sql"])
    assert [r[0] for r in result["rows"]] == ["A", "B"]
    assert [r[result["columns"].index("posicao")] for r in result["rows"]] == [1, 2]
