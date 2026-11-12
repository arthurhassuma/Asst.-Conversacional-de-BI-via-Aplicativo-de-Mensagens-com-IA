import calendar
from datetime import date, timedelta
from decimal import Decimal
from random import Random

from faker import Faker

CLIENT_SUFFIXES = ("Ltda", "S.A.", "EIRELI", "Soluções", "Tecnologia", "Consultoria", "Serviços")
CONTRACT_DESCRIPTIONS = (
    "Desenvolvimento de sistema",
    "Sustentação de aplicações",
    "Consultoria técnica",
    "Integração de sistemas",
    "Modernização de plataforma",
)
ORDER_DESCRIPTIONS = (
    "Entrega mensal de serviço",
    "Sprint de desenvolvimento",
    "Ciclo de sustentação mensal",
    "Pacote de horas de consultoria",
    "Entrega de incremento do projeto",
    "Revisão e suporte mensal",
)
CITIES = (
    ("Joinville", "SC"),
    ("Blumenau", "SC"),
    ("Curitiba", "PR"),
    ("Florianópolis", "SC"),
    ("São Paulo", "SP"),
    ("Porto Alegre", "RS"),
)
SEGMENTS = ("Indústria", "Tecnologia", "Logística", "Serviços", "Varejo", "Educação")


def generate_data_v2(seed: int = 42, clients: int = 30) -> dict[str, list[dict]]:
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
        city, state = CITIES[rng.randrange(len(CITIES))]
        data["clientes"].append(
            dict(
                id=client_id,
                nome=f"Empresa Fictícia {fake.company()} {rng.choice(CLIENT_SUFFIXES)}",
                segmento=rng.choice(SEGMENTS),
                cidade=city,
                uf=state,
                cadastrado_em=date(2023, 1, 1) + timedelta(days=rng.randrange(300)),
            )
        )
        for _ in range(rng.randint(1, 3)):
            contract_id = len(data["contratos"]) + 1
            year = rng.choice([2024, 2025])
            base = Decimal(rng.randrange(500000, 3000000)) / 100
            contract = dict(
                id=contract_id,
                cliente_id=client_id,
                descricao=rng.choice(CONTRACT_DESCRIPTIONS),
                modalidade=rng.choice(["projeto", "sustentacao"]),
                inicio=date(year, 1, 1),
                fim=date(year, 12, 31),
                valor_contratado=Decimal("0.00"),
                status="concluido",
            )
            data["contratos"].append(contract)
            for month in range(1, 13):
                order_id = len(data["pedidos"]) + 1
                day = 1 + rng.randrange(calendar.monthrange(year, month)[1])
                order_date = date(year, month, day)
                monthly = (base * Decimal(rng.randint(85, 115)) / 100).quantize(Decimal("0.01"))
                cancelled = rng.random() < 0.06
                data["pedidos"].append(
                    dict(
                        id=order_id,
                        contrato_id=contract_id,
                        descricao=rng.choice(ORDER_DESCRIPTIONS),
                        data_pedido=order_date,
                        valor=monthly,
                        status="cancelado" if cancelled else "entregue",
                    )
                )
                if not cancelled:
                    contract["valor_contratado"] += monthly
                    invoice_id = len(data["faturamento"]) + 1
                    emission = order_date + timedelta(days=rng.randint(5, 15))
                    paid = rng.random() < 0.88
                    data["faturamento"].append(
                        dict(
                            id=invoice_id,
                            pedido_id=order_id,
                            numero_documento=f"SINTV2-{invoice_id:06d}",
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
            if contract["valor_contratado"] <= 0:
                contract["valor_contratado"] = base
    return data


def day_coverage_report(data: dict) -> dict:
    orders = data["pedidos"]
    days = {row["data_pedido"].day for row in orders}
    descriptions = {row["descricao"] for row in orders}
    values = {row["valor"] for row in orders}
    if len(days) < 15:
        raise ValueError(f"Cobertura de dias insuficiente: apenas {len(days)} dias distintos.")
    if len(descriptions) < 3:
        raise ValueError(f"Descrições pouco variadas: apenas {len(descriptions)} distintas.")
    if len(values) < len(orders) // 2:
        raise ValueError("Valores repetidos em excesso entre os pedidos.")
    return {
        "pedidos": len(orders),
        "dias_distintos": len(days),
        "descricoes_distintas": len(descriptions),
        "valores_distintos": len(values),
    }


def generate_data(
    seed: int = 42,
    clients: int = 30,
    *,
    profile: str = "original",
    start_month: str = "2025-01",
    end_month: str = "2026-10",
) -> dict[str, list[dict]]:
    if profile == "autopecas":
        from scripts.autopecas_seed import generate_autopecas_data

        return generate_autopecas_data(seed, clients, start_month, end_month)
    if profile in ("comparativo", "comparativo-v2"):
        from scripts.comparative_seed import generate_comparative_data

        version = "v2" if profile == "comparativo-v2" else "v1"
        return generate_comparative_data(seed, clients, start_month, end_month, version=version)
    if profile == "original-v2":
        return generate_data_v2(seed, clients)
    if profile != "original":
        raise ValueError(
            "Perfil desconhecido. Use original, original-v2, comparativo, comparativo-v2 ou autopecas."
        )
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
