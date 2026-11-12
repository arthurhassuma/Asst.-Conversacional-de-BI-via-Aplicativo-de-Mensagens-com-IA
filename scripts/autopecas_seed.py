import calendar
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from random import Random

from faker import Faker

from app.domain import CITIES
from scripts.comparative_seed import TABLE_DATES, month_end, month_range

PROFILE = "autopecas-v1"
INITIAL_PORTFOLIO = 70
MONTHLY_SUPPLY_CLIENTS = 12
CITY_WEIGHTS = (22, 14, 10, 9, 6, 10, 8, 4, 10, 7)
SEASONALITY = (92, 95, 100, 102, 100, 98, 103, 104, 102, 106, 108, 96)
ANNUAL_GROWTH = Decimal("0.04")
LOCAIS = (
    "Vale do Itajaí", "Santa Cruz", "Boa Vista", "Água Verde", "Bom Retiro",
    "Costa e Silva", "Itaum", "Atiradores", "Centro Sul", "Norte Catarinense",
    "Três Rios", "Vila Nova", "Floresta", "São Marcos", "Bom Jesus", "Serra Azul",
)  # fmt: skip

SEGMENTS = {
    "Oficina mecânica": {
        "weight": 34,
        "ticket": 430,
        "orders": (2, 6),
        "terms": (15, 28),
        "names": (
            "Auto Mecânica {sobrenome}",
            "Oficina {sobrenome}",
            "Mecânica {sobrenome} & Filhos",
            "Centro Automotivo {local}",
        ),
        "items": (
            "Pastilhas e discos de freio",
            "Kit de embreagem",
            "Filtros de óleo, ar e combustível",
            "Amortecedores dianteiros",
            "Correia dentada com tensor",
            "Velas e cabos de ignição",
            "Juntas e retentores",
            "Bomba d'água e válvula termostática",
            "Pivôs e terminais de direção",
            "Rolamentos de roda",
        ),
        "contracts": (
            "Fornecimento mensal de peças de reposição",
            "Reposição programada de peças — linha leve",
        ),
        "projects": ("Kit para revisão preventiva", "Peças para retífica e reparo de motor"),
    },
    "Auto elétrica": {
        "weight": 10,
        "ticket": 340,
        "orders": (1, 4),
        "terms": (15, 21),
        "names": ("Auto Elétrica {sobrenome}", "Elétrica Automotiva {local}"),
        "items": (
            "Baterias 60Ah e 70Ah",
            "Alternador remanufaturado",
            "Motor de partida",
            "Bobinas de ignição",
            "Sensores e sondas lambda",
            "Lâmpadas e faróis",
        ),
        "contracts": ("Fornecimento mensal de componentes elétricos",),
        "projects": ("Lote de baterias e alternadores",),
    },
    "Funilaria e pintura": {
        "weight": 8,
        "ticket": 740,
        "orders": (1, 4),
        "terms": (21, 28),
        "names": ("Funilaria e Pintura {sobrenome}", "Martelinho {sobrenome}", "Funilaria {local}"),
        "items": (
            "Para-choques e grades",
            "Faróis e lanternas",
            "Retrovisores",
            "Tinta automotiva e verniz",
            "Massa e aditivos de pintura",
            "Capô e paralamas",
        ),
        "contracts": ("Fornecimento mensal de peças de lataria e tintas",),
        "projects": ("Peças de lataria para reparo de sinistro",),
    },
    "Autocenter": {
        "weight": 12,
        "ticket": 800,
        "orders": (3, 8),
        "terms": (21, 30),
        "names": ("Autocenter {local}", "{local} Auto Center", "Pneus {sobrenome}"),
        "items": (
            "Pneus aro 15 e 16",
            "Amortecedores e kits de suspensão",
            "Óleo lubrificante e filtros",
            "Baterias",
            "Pastilhas e discos de freio",
            "Alinhamento e balanceamento — contrapesos e válvulas",
        ),
        "contracts": ("Abastecimento recorrente de pneus, óleo e suspensão",),
        "projects": ("Lote de pneus para campanha de inverno",),
    },
    "Frota e transportadora": {
        "weight": 14,
        "ticket": 1700,
        "orders": (1, 4),
        "terms": (30, 45),
        "names": (
            "Transportadora {sobrenome}",
            "{sobrenome} Logística e Transportes",
            "Rota {local} Transportes",
            "Expresso {local}",
        ),
        "items": (
            "Pneus aro 22,5",
            "Pastilhas e lonas de freio — linha pesada",
            "Filtros — linha pesada",
            "Óleo lubrificante 15W40 (tambor)",
            "Kit de embreagem — linha pesada",
            "Molas e amortecedores",
            "Baterias estacionárias",
        ),
        "contracts": ("Fornecimento de peças e lubrificantes para frota",),
        "projects": ("Kit de revisão de frota", "Peças para parada programada da frota"),
    },
    "Loja de autopeças": {
        "weight": 16,
        "ticket": 1380,
        "orders": (2, 6),
        "terms": (28, 30),
        "names": ("Auto Peças {sobrenome}", "Peças {local}", "{sobrenome} Auto Peças"),
        "items": (
            "Reposição de estoque — linha leve",
            "Filtros (lote)",
            "Aditivos e fluidos (lote)",
            "Pastilhas de freio (lote)",
            "Lâmpadas (lote)",
            "Palhetas e acessórios",
        ),
        "contracts": ("Abastecimento recorrente de estoque para revenda",),
        "projects": ("Lote de peças para estoque de alta temporada",),
    },
    "Retífica de motores": {
        "weight": 6,
        "ticket": 1100,
        "orders": (1, 3),
        "terms": (21, 28),
        "names": ("Retífica {sobrenome}", "Retífica de Motores {local}"),
        "items": (
            "Kit de retífica de motor",
            "Bielas, bronzinas e anéis",
            "Cabeçote e juntas",
            "Bomba de óleo",
            "Válvulas e guias",
        ),
        "contracts": ("Fornecimento mensal de componentes de motor",),
        "projects": ("Componentes para retífica completa",),
    },
}
REQUIRED_STATUSES = {
    "contratos": set(),
    "pedidos": {"entregue", "cancelado"},
    "faturamento": {"paga", "cancelada"},
}


def _client_name(rng, fake, segment, city, used):
    templates = SEGMENTS[segment]["names"]
    for _ in range(40):
        name = rng.choice(templates).format(sobrenome=fake.last_name(), local=rng.choice(LOCAIS))
        if name not in used:
            break
    else:
        name = f"{name} — {city}"
    used.add(name)
    return name


def _cents_to_decimal(cents: int) -> Decimal:
    return Decimal(cents) / 100


def generate_autopecas_data(seed: int, clients: int, start: str, end: str) -> dict:
    months = month_range(start, end)
    if not INITIAL_PORTFOLIO + len(months) <= clients <= 1000:
        raise ValueError(
            f"O perfil autopecas exige entre {INITIAL_PORTFOLIO + len(months)} e mil clientes "
            "para garantir cadastros mensais e a carteira inicial."
        )
    cutoff = month_end(months[-1])
    fake, rng = Faker("pt_BR"), Random(seed)
    fake.seed_instance(seed)
    data = {name: [] for name in TABLE_DATES}
    month_orders, month_invoices = Counter(), Counter()
    used_names: set[str] = set()
    segment_names = list(SEGMENTS)
    segment_weights = [SEGMENTS[name]["weight"] for name in segment_names]

    def growth(month: date) -> Decimal:
        elapsed = (month.year - months[0].year) * 12 + month.month - months[0].month
        return Decimal(SEASONALITY[month.month - 1]) / 100 * (1 + ANNUAL_GROWTH * elapsed / 12)

    def add_invoices(order, segment, status):
        cents = int(order["valor"] * 100)
        parts = (
            [cents // 2, cents - cents // 2] if cents >= 40_000 and rng.random() < 0.12 else [cents]
        )
        for part, amount in enumerate(parts):
            emitted = min(order["data_pedido"] + timedelta(days=rng.randint(0, 2) + part), cutoff)
            due = emitted + timedelta(days=rng.choice(SEGMENTS[segment]["terms"]))
            paid_on = max(
                emitted, due + timedelta(days=rng.choice((-3, -2, 0, 0, 0, 1, 2, 4, 7, 12, 20)))
            )
            key = (emitted.year, emitted.month)
            month_invoices[key] += 1
            if status == "aprovado":
                invoice_status = "aberta"
            elif month_invoices[key] == 7 or rng.random() < 0.015:
                invoice_status = "cancelada"
            elif paid_on <= cutoff and rng.random() > 0.025:
                invoice_status = "paga"
            else:
                invoice_status = "aberta"
            invoice_id = len(data["faturamento"]) + 1
            data["faturamento"].append(
                dict(
                    id=invoice_id,
                    pedido_id=order["id"],
                    numero_documento=f"NF-{18000 + invoice_id:06d}",
                    emissao=emitted,
                    vencimento=due,
                    pagamento=paid_on if invoice_status == "paga" else None,
                    valor=_cents_to_decimal(amount),
                    status=invoice_status,
                )
            )

    def add_activity(contract, active_months, segment, size, *, project=False):
        profile = SEGMENTS[segment]
        total_cents = 0
        for month in active_months:
            factor = growth(month)
            first_month = (month.year, month.month) == (
                contract["inicio"].year,
                contract["inicio"].month,
            )
            last_day = calendar.monthrange(month.year, month.month)[1]
            lo, hi = profile["orders"]
            if project:
                count = rng.randint(1, 2)
            else:
                count = max(1, int(rng.randint(lo, hi) * size * float(factor) + rng.random()))
            days = [
                d
                for d in range(contract["inicio"].day if first_month else 1, last_day + 1)
                if date(month.year, month.month, d).weekday() != 6
            ] or [last_day]
            for _ in range(count):
                ordered = date(month.year, month.month, rng.choice(days))
                ticket = profile["ticket"] * (1.9 if project else 1.0) * float(factor)
                cents = max(6000, int(ticket * rng.lognormvariate(0, 0.6) * 100)) // 5 * 5
                month_orders[(month.year, month.month)] += 1
                if month_orders[(month.year, month.month)] == 5 or rng.random() < 0.03:
                    status = "cancelado"
                elif ordered >= cutoff - timedelta(days=4) and rng.random() < 0.55:
                    status = "aprovado"
                else:
                    status = "entregue"
                order = dict(
                    id=len(data["pedidos"]) + 1,
                    contrato_id=contract["id"],
                    descricao=rng.choice(profile["items"]),
                    data_pedido=ordered,
                    valor=_cents_to_decimal(cents),
                    status=status,
                )
                data["pedidos"].append(order)
                total_cents += cents
                if status != "cancelado":
                    add_invoices(order, segment, status)
            if contract["inicio"].day == 1 or not first_month:
                opened = sum(rng.random() < 0.06 for _ in range(count))
                planned = (2 if project else 4) + 2 * count + rng.randint(0, 4)
                performed_pct = rng.randint(78, 128)
                rate = rng.randint(70, 98)
                resolver = Random(f"{seed}-{contract['id']}-{month:%Y%m}")
                resolved = sum(resolver.random() * 100 < rate for _ in range(opened))
                data["indicadores_operacionais"].append(
                    dict(
                        id=len(data["indicadores_operacionais"]) + 1,
                        contrato_id=contract["id"],
                        competencia=month,
                        horas_previstas=Decimal(planned),
                        horas_realizadas=Decimal(planned * performed_pct) / 100,
                        chamados_abertos=opened,
                        chamados_resolvidos=resolved,
                    )
                )
        contract["valor_contratado"] = _cents_to_decimal(max(total_cents, 1) * 105 // 100)

    for client_id in range(1, clients + 1):
        segment = rng.choices(segment_names, segment_weights)[0]
        city, state = rng.choices(CITIES, CITY_WEIGHTS)[0]
        if client_id <= INITIAL_PORTFOLIO:
            registered = months[0] - timedelta(days=rng.randint(60, 900))
        else:
            month = months[(client_id - INITIAL_PORTFOLIO - 1) % len(months)]
            registered = month.replace(day=rng.randint(1, 28))
        data["clientes"].append(
            dict(
                id=client_id,
                nome=_client_name(rng, fake, segment, city, used_names),
                segmento=segment,
                cidade=city,
                uf=state,
                cadastrado_em=registered,
            )
        )
        size = min(2.2, max(0.5, rng.lognormvariate(0, 0.35)))
        relationship = (
            "ativo"
            if client_id <= MONTHLY_SUPPLY_CLIENTS
            else rng.choices(("ativo", "cancelado", "concluido"), (85, 8, 7))[0]
        )
        eligible = [m for m in months if month_end(m) >= registered]
        if relationship != "ativo":
            eligible = eligible[: rng.randint(min(3, len(eligible)), len(eligible))]
        recurring = dict(
            id=len(data["contratos"]) + 1,
            cliente_id=client_id,
            descricao=rng.choice(SEGMENTS[segment]["contracts"]),
            modalidade="sustentacao",
            inicio=eligible[0] if client_id <= INITIAL_PORTFOLIO else registered,
            fim=date(cutoff.year + 1, 12, 31)
            if relationship == "ativo"
            else month_end(eligible[-1]),
            valor_contratado=Decimal("0.00"),
            status=relationship,
        )
        data["contratos"].append(recurring)
        add_activity(recurring, eligible, segment, size)
        project_months = (
            months if client_id <= MONTHLY_SUPPLY_CLIENTS else eligible[1 + client_id % 4 :: 4]
        )
        for month in project_months:
            recent = month_end(month) >= cutoff - timedelta(days=60)
            project = dict(
                id=len(data["contratos"]) + 1,
                cliente_id=client_id,
                descricao=rng.choice(SEGMENTS[segment]["projects"]),
                modalidade="projeto",
                inicio=month,
                fim=cutoff + timedelta(days=60) if recent else month_end(month),
                valor_contratado=Decimal("0.00"),
                status="cancelado" if rng.random() < 0.07 else ("ativo" if recent else "concluido"),
            )
            data["contratos"].append(project)
            add_activity(project, [month], segment, size, project=True)
    return data


def sales_summary(data: dict) -> dict:
    sold: dict[int, Decimal] = {}
    count: Counter = Counter()
    for order in data["pedidos"]:
        if order["status"] != "cancelado":
            year = order["data_pedido"].year
            sold[year] = sold.get(year, Decimal("0")) + order["valor"]
            count[year] += 1
    months_by_year = Counter(
        {
            y: len({o["data_pedido"].month for o in data["pedidos"] if o["data_pedido"].year == y})
            for y in sold
        }
    )
    return {
        str(year): {
            "pedidos": count[year],
            "valor_pedidos": format(sold[year], ".2f"),
            "media_mensal_pedidos": round(count[year] / months_by_year[year]),
            "media_mensal_valor": format(sold[year] / months_by_year[year], ".2f"),
            "ticket_medio": format(sold[year] / count[year], ".2f"),
        }
        for year in sorted(sold)
    }
