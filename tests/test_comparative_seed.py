from collections import defaultdict
from datetime import date
from decimal import Decimal

import pytest

from scripts.seed import generate_data


def comparative(**kwargs):
    return generate_data(seed=42, clients=100, profile="comparativo", **kwargs)


def test_comparative_seed_covers_every_month_and_status_reproducibly():
    data = comparative()
    assert data == comparative()
    months = {f"2025-{m:02}" for m in range(1, 13)} | {f"2026-{m:02}" for m in range(1, 11)}
    for table, field, statuses in (
        ("clientes", "cadastrado_em", None),
        ("contratos", "inicio", {"ativo", "concluido", "cancelado"}),
        ("pedidos", "data_pedido", {"aprovado", "entregue", "cancelado"}),
        ("faturamento", "emissao", {"paga", "aberta", "cancelada"}),
        ("indicadores_operacionais", "competencia", None),
    ):
        grouped = defaultdict(list)
        for row in data[table]:
            grouped[row[field].strftime("%Y-%m")].append(row)
        assert months <= grouped.keys(), table
        for month in months:
            if statuses:
                assert {r["status"] for r in grouped[month]} == statuses, (table, month)
    assert len(data["clientes"]) == 100
    assert len(data["pedidos"]) > 3000
    assert len({r["valor"] for r in data["pedidos"]}) > 100
    assert {
        r["pagamento"].strftime("%Y-%m") for r in data["faturamento"] if r["pagamento"]
    } == months


def test_comparative_financial_and_temporal_integrity():
    data = comparative()
    clients = {r["id"]: r for r in data["clientes"]}
    contracts = {r["id"]: r for r in data["contratos"]}
    orders = {r["id"]: r for r in data["pedidos"]}
    ordered, billed = defaultdict(Decimal), defaultdict(Decimal)
    for contract in contracts.values():
        assert contract["inicio"] >= clients[contract["cliente_id"]]["cadastrado_em"]
        if contract["status"] == "ativo":
            assert contract["fim"] > date(2026, 10, 31)
    for order in orders.values():
        contract = contracts[order["contrato_id"]]
        assert contract["inicio"] <= order["data_pedido"] <= contract["fim"]
        if order["status"] != "cancelado":
            ordered[contract["id"]] += order["valor"]
    for invoice in data["faturamento"]:
        order = orders[invoice["pedido_id"]]
        assert order["status"] != "cancelado"
        assert order["data_pedido"] <= invoice["emissao"] <= invoice["vencimento"]
        assert (invoice["status"] == "paga") == (invoice["pagamento"] is not None)
        if invoice["pagamento"]:
            assert invoice["emissao"] <= invoice["pagamento"] <= date(2026, 10, 31)
        if invoice["status"] != "cancelada":
            billed[order["id"]] += invoice["valor"]
    assert all(v <= orders[k]["valor"] for k, v in billed.items())
    assert all(v <= contracts[k]["valor_contratado"] for k, v in ordered.items())
    for row in data["indicadores_operacionais"]:
        contract = contracts[row["contrato_id"]]
        assert contract["inicio"] <= row["competencia"] <= contract["fim"]
        assert 0 <= row["chamados_resolvidos"] <= row["chamados_abertos"]
    assert any(r["chamados_abertos"] == 0 for r in data["indicadores_operacionais"])


@pytest.mark.parametrize(
    "kwargs", [{"start_month": "2026-11", "end_month": "2026-10"}, {"start_month": "2025-13"}]
)
def test_invalid_comparative_period_is_rejected(kwargs):
    with pytest.raises(ValueError):
        comparative(**kwargs)


def test_coverage_report_rejects_a_missing_month_or_status():
    from scripts.comparative_seed import coverage_report

    data = comparative()
    report = coverage_report(data)
    assert report["meses"] == 22
    assert report["fotografia_status"] == "2026-10-31"
    assert report["mensal"][-1]["mes"] == "2026-10"
    data["faturamento"] = [
        r
        for r in data["faturamento"]
        if not (
            r["emissao"].year == 2026 and r["emissao"].month == 10 and r["status"] == "cancelada"
        )
    ]
    with pytest.raises(ValueError, match="Status incompletos em faturamento"):
        coverage_report(data)


def test_comparative_minimum_clients_and_unknown_profile_are_rejected():
    with pytest.raises(ValueError, match="34"):
        generate_data(clients=33, profile="comparativo")
    with pytest.raises(ValueError, match="Perfil desconhecido"):
        generate_data(profile="inexistente")


def test_comparative_v1_still_matches_frozen_day_window_and_descriptions():
    """Trava de regressão: comparativo (v1) alimenta docs/projeto.md com
    hash publicado; não pode mudar, mesmo ao corrigir a variedade no v2."""
    data = comparative()
    assert {row["data_pedido"].day for row in data["pedidos"]} <= set(range(2, 19))
    assert {row["descricao"] for row in data["pedidos"]} == {
        "Marco de projeto",
        "Serviço de sustentação",
    }
    assert {row["descricao"] for row in data["contratos"]} == {
        "Sustentação mensal de aplicações",
        "Projeto de melhoria e integração",
    }


def comparative_v2(**kwargs):
    return generate_data(seed=42, clients=100, profile="comparativo-v2", **kwargs)


def test_comparative_v2_is_reproducible_and_passes_existing_coverage_report():
    from scripts.comparative_seed import coverage_report

    data = comparative_v2()
    assert data == comparative_v2()
    report = coverage_report(data)
    assert report["meses"] == 22
    assert len(data["clientes"]) == 100


def test_comparative_v2_fixes_day_and_description_repetition():
    from scripts.seed import day_coverage_report

    data = comparative_v2()
    report = day_coverage_report(data)
    assert report["dias_distintos"] > 18
    assert report["descricoes_distintas"] >= 3
    descriptions = {row["descricao"] for row in data["contratos"]}
    assert len(descriptions) >= 3
