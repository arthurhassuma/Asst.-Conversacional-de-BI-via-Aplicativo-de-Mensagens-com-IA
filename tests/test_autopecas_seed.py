from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

import pytest

from app.domain import CITIES
from scripts.autopecas_seed import PROFILE, REQUIRED_STATUSES, SEGMENTS, sales_summary
from scripts.comparative_seed import coverage_report
from scripts.seed import generate_data

CUTOFF = date(2026, 10, 31)


@pytest.fixture(scope="module")
def data():
    return generate_data(seed=42, clients=100, profile="autopecas")


def test_profile_is_reproducible_and_seed_sensitive(data):
    assert data == generate_data(seed=42, clients=100, profile="autopecas")
    other = generate_data(seed=7, clients=100, profile="autopecas")
    assert [c["nome"] for c in data["clientes"]] != [c["nome"] for c in other["clientes"]]


def test_client_names_look_like_auto_parts_customers_and_are_unique(data):
    names = [c["nome"] for c in data["clientes"]]
    assert len(set(names)) == len(names) == 100
    assert not any("fictíci" in n.lower() or "ltda" in n.lower() for n in names)
    assert {c["segmento"] for c in data["clientes"]} <= set(SEGMENTS)
    assert len({c["segmento"] for c in data["clientes"]}) >= 5
    assert {(c["cidade"], c["uf"]) for c in data["clientes"]} <= set(CITIES)
    assert any(
        word in n
        for n in names
        for word in ("Auto", "Oficina", "Mecânica", "Transport", "Funilaria")
    )


def test_orders_use_parts_vocabulary_not_software_services(data):
    descriptions = {o["descricao"] for o in data["pedidos"]} | {
        c["descricao"] for c in data["contratos"]
    }
    text = " ".join(descriptions).lower()
    assert len(descriptions) > 25
    for word in ("sprint", "software", "sustentação de aplic", "desenvolvimento"):
        assert word not in text
    assert any("freio" in d.lower() for d in descriptions)


def test_scale_matches_a_small_to_medium_reseller(data):
    summary = sales_summary(data)
    for year in ("2025", "2026"):
        monthly = Decimal(summary[year]["media_mensal_valor"])
        ticket = Decimal(summary[year]["ticket_medio"])
        assert Decimal("250000") <= monthly <= Decimal("600000"), summary[year]
        assert Decimal("700") <= ticket <= Decimal("1800"), summary[year]
        assert 200 <= summary[year]["media_mensal_pedidos"] <= 500
    values = [o["valor"] for o in data["pedidos"]]
    assert min(values) >= Decimal("60") and max(values) < Decimal("40000")
    assert len({o["data_pedido"].day for o in data["pedidos"]}) >= 25


def test_orders_per_client_are_not_uniform(data):
    contract_client = {c["id"]: c["cliente_id"] for c in data["contratos"]}
    per_client = Counter(
        contract_client[o["contrato_id"]]
        for o in data["pedidos"]
        if o["status"] != "cancelado"
        and (o["data_pedido"].year, o["data_pedido"].month) == (2026, 9)
    )
    assert len(set(per_client.values())) >= 5


def test_monthly_coverage_with_realistic_statuses(data):
    report = coverage_report(
        data, "2025-01", "2026-10", required=REQUIRED_STATUSES, profile=PROFILE
    )
    assert report["perfil"] == PROFILE and report["meses"] == 22
    approved = [o for o in data["pedidos"] if o["status"] == "aprovado"]
    assert approved and all(o["data_pedido"] >= date(2026, 10, 27) for o in approved)


def test_financial_and_temporal_integrity(data):
    clients = {r["id"]: r for r in data["clientes"]}
    contracts = {r["id"]: r for r in data["contratos"]}
    orders = {r["id"]: r for r in data["pedidos"]}
    ordered, billed = defaultdict(Decimal), defaultdict(Decimal)
    assert {c["cliente_id"] for c in contracts.values()} == set(clients)
    for contract in contracts.values():
        assert contract["inicio"] >= clients[contract["cliente_id"]]["cadastrado_em"]
        assert contract["valor_contratado"] > 0
    for order in orders.values():
        contract = contracts[order["contrato_id"]]
        assert contract["inicio"] <= order["data_pedido"] <= contract["fim"]
        assert order["data_pedido"] <= CUTOFF
        if order["status"] != "cancelado":
            ordered[contract["id"]] += order["valor"]
    for invoice in data["faturamento"]:
        order = orders[invoice["pedido_id"]]
        assert order["status"] != "cancelado"
        assert order["data_pedido"] <= invoice["emissao"] <= invoice["vencimento"]
        assert (invoice["status"] == "paga") == (invoice["pagamento"] is not None)
        if invoice["pagamento"]:
            assert invoice["emissao"] <= invoice["pagamento"] <= CUTOFF
        if invoice["status"] != "cancelada":
            billed[order["id"]] += invoice["valor"]
    assert all(v <= orders[k]["valor"] for k, v in billed.items())
    assert all(v <= contracts[k]["valor_contratado"] for k, v in ordered.items())
    assert len({r["numero_documento"] for r in data["faturamento"]}) == len(data["faturamento"])
    for row in data["indicadores_operacionais"]:
        contract = contracts[row["contrato_id"]]
        assert contract["inicio"] <= row["competencia"] <= contract["fim"]
        assert 0 <= row["chamados_resolvidos"] <= row["chamados_abertos"]
        assert row["horas_previstas"] > 0


def test_only_schema_allowed_values_are_generated(data):
    assert {c["modalidade"] for c in data["contratos"]} == {"projeto", "sustentacao"}
    assert {c["status"] for c in data["contratos"]} <= {"ativo", "concluido", "cancelado"}
    assert {o["status"] for o in data["pedidos"]} <= {"aprovado", "entregue", "cancelado"}
    assert {i["status"] for i in data["faturamento"]} <= {"aberta", "paga", "cancelada"}


def test_too_few_clients_for_the_monthly_registrations_is_rejected():
    with pytest.raises(ValueError, match="exige entre"):
        generate_data(seed=42, clients=40, profile="autopecas")


def test_after_sales_resolution_rate_is_realistic(data):
    rows = data["indicadores_operacionais"]
    opened = sum(r["chamados_abertos"] for r in rows)
    resolved = sum(r["chamados_resolvidos"] for r in rows)
    assert opened > 300
    assert 0.75 <= resolved / opened <= 0.95
    sept = [r for r in rows if (r["competencia"].year, r["competencia"].month) == (2026, 9)]
    assert sum(r["chamados_resolvidos"] for r in sept) >= 10
