import pytest

from scripts.seed import day_coverage_report, generate_data


def test_seed_is_reproducible_and_relations_are_consistent():
    data = generate_data(seed=42, clients=5)
    assert data == generate_data(seed=42, clients=5)
    assert len(data["clientes"]) == 5
    clients = {row["id"] for row in data["clientes"]}
    contracts = {row["id"]: row for row in data["contratos"]}
    orders = {row["id"]: row for row in data["pedidos"]}
    assert {c["cliente_id"] for c in contracts.values()} == clients
    for order in orders.values():
        contract = contracts[order["contrato_id"]]
        assert contract["inicio"] <= order["data_pedido"] <= contract["fim"]
        assert order["valor"] > 0
    billed = {}
    for invoice in data["faturamento"]:
        order = orders[invoice["pedido_id"]]
        assert order["data_pedido"] <= invoice["emissao"] <= invoice["vencimento"]
        if invoice["pagamento"]:
            assert invoice["pagamento"] >= invoice["emissao"]
        if invoice["status"] != "cancelada":
            billed[order["id"]] = billed.get(order["id"], 0) + invoice["valor"]
    assert all(value <= orders[key]["valor"] for key, value in billed.items())
    for indicator in data["indicadores_operacionais"]:
        assert indicator["contrato_id"] in contracts
        assert indicator["chamados_resolvidos"] <= indicator["chamados_abertos"]


def test_original_profile_still_matches_frozen_single_day_and_description():
    """Trava de regressão: o perfil original não pode mudar, pois alimenta a
    avaliação congelada de 40 casos com SQL de referência já publicados."""
    data = generate_data(seed=42, clients=5, profile="original")
    assert {row["data_pedido"].day for row in data["pedidos"]} == {5}
    assert {row["descricao"] for row in data["pedidos"]} == {"Entrega mensal de serviço"}


def test_original_v2_profile_is_reproducible_and_relations_are_consistent():
    data = generate_data(seed=42, clients=30, profile="original-v2")
    assert data == generate_data(seed=42, clients=30, profile="original-v2")
    clients = {row["id"] for row in data["clientes"]}
    contracts = {row["id"]: row for row in data["contratos"]}
    orders = {row["id"]: row for row in data["pedidos"]}
    assert {c["cliente_id"] for c in contracts.values()} == clients
    for order in orders.values():
        contract = contracts[order["contrato_id"]]
        assert contract["inicio"] <= order["data_pedido"] <= contract["fim"]
        assert order["valor"] > 0
    for contract in contracts.values():
        assert contract["valor_contratado"] > 0
    billed = {}
    for invoice in data["faturamento"]:
        order = orders[invoice["pedido_id"]]
        assert order["data_pedido"] <= invoice["emissao"] <= invoice["vencimento"]
        if invoice["pagamento"]:
            assert invoice["pagamento"] >= invoice["emissao"]
        if invoice["status"] != "cancelada":
            billed[order["id"]] = billed.get(order["id"], 0) + invoice["valor"]
    assert all(value <= orders[key]["valor"] for key, value in billed.items())
    for indicator in data["indicadores_operacionais"]:
        assert indicator["contrato_id"] in contracts
        assert indicator["chamados_resolvidos"] <= indicator["chamados_abertos"]


def test_original_v2_profile_fixes_day_description_and_value_repetition():
    data = generate_data(seed=42, clients=30, profile="original-v2")
    report = day_coverage_report(data)
    assert report["dias_distintos"] >= 15
    assert report["descricoes_distintas"] >= 3
    assert report["valores_distintos"] >= report["pedidos"] // 2
    names = [row["nome"] for row in data["clientes"]]
    assert len(set(names)) == len(names)


def test_day_coverage_report_rejects_the_original_profile_pattern():
    data = generate_data(seed=42, clients=5, profile="original")
    with pytest.raises(ValueError):
        day_coverage_report(data)
