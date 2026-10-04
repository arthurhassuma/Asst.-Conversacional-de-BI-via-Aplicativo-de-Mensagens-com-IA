from scripts.seed import generate_data


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
