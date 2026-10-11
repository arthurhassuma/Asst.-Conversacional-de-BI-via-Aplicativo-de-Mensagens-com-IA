"""Geração determinística: centavos inteiros, datas fixas e Faker com seed local."""

from datetime import date, timedelta
from decimal import Decimal
from random import Random

from faker import Faker


def generate_data(
    seed: int = 42,
    clients: int = 30,
    *,
    profile: str = "original",
    start_month: str = "2025-01",
    end_month: str = "2026-10",
) -> dict[str, list[dict]]:
    if profile == "comparativo":
        from scripts.comparative_seed import generate_comparative_data

        return generate_comparative_data(seed, clients, start_month, end_month)
    if profile != "original":
        raise ValueError("Perfil desconhecido. Use original ou comparativo.")
    if not 1 <= clients <= 1000:
        raise ValueError("A quantidade de clientes deve estar entre um e mil.")
    fake = Faker("pt_BR")
    fake.seed_instance(seed)
    rng = Random(seed)
    data = {
        name: []
        for name in ("clientes", "contratos", "pedidos", "faturamento", "indicadores_operacionais")
    }
    for client_id in range(1, clients + 1):
        data["clientes"].append(
            dict(
                id=client_id,
                nome=f"Empresa Fictícia {fake.company()}",
                segmento=rng.choice(["Indústria", "Tecnologia", "Logística", "Serviços"]),
                cidade=rng.choice(["Joinville", "Blumenau", "Curitiba", "Florianópolis"]),
                uf="SC",
                cadastrado_em=date(2023, 1, 1) + timedelta(days=rng.randrange(300)),
            )
        )
        # Mantém UF coerente com a cidade sintética.
        if data["clientes"][-1]["cidade"] == "Curitiba":
            data["clientes"][-1]["uf"] = "PR"
        for _ in range(rng.randint(1, 3)):
            contract_id = len(data["contratos"]) + 1
            year = rng.choice([2024, 2025])
            start, end = date(year, 1, 1), date(year, 12, 31)
            monthly = Decimal(rng.randrange(500000, 3000000)) / 100
            data["contratos"].append(
                dict(
                    id=contract_id,
                    cliente_id=client_id,
                    descricao=rng.choice(
                        ["Desenvolvimento de sistema", "Sustentação de aplicações"]
                    ),
                    modalidade=rng.choice(["projeto", "sustentacao"]),
                    inicio=start,
                    fim=end,
                    valor_contratado=monthly * 12,
                    status="concluido",
                )
            )
            for month in range(1, 13):
                order_id = len(data["pedidos"]) + 1
                order_date = date(year, month, 5)
                cancelled = rng.random() < 0.06
                data["pedidos"].append(
                    dict(
                        id=order_id,
                        contrato_id=contract_id,
                        descricao="Entrega mensal de serviço",
                        data_pedido=order_date,
                        valor=monthly,
                        status="cancelado" if cancelled else "entregue",
                    )
                )
                if not cancelled:
                    invoice_id = len(data["faturamento"]) + 1
                    emission = order_date + timedelta(days=10)
                    paid = rng.random() < 0.88
                    data["faturamento"].append(
                        dict(
                            id=invoice_id,
                            pedido_id=order_id,
                            numero_documento=f"SINT-{invoice_id:06d}",
                            emissao=emission,
                            vencimento=emission + timedelta(days=30),
                            pagamento=emission + timedelta(days=rng.randint(5, 40))
                            if paid
                            else None,
                            valor=monthly,
                            status="paga" if paid else "aberta",
                        )
                    )
                opened = rng.randrange(1, 50)
                data["indicadores_operacionais"].append(
                    dict(
                        id=len(data["indicadores_operacionais"]) + 1,
                        contrato_id=contract_id,
                        competencia=date(year, month, 1),
                        horas_previstas=Decimal(rng.randrange(80, 201)),
                        horas_realizadas=Decimal(rng.randrange(6000, 22001)) / 100,
                        chamados_abertos=opened,
                        chamados_resolvidos=rng.randint(0, opened),
                    )
                )
    return data
