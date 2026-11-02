"""Cenário sintético para comparação mensal, separado da base experimental original.

Valores em centavos inteiros. A cobertura mínima é determinística, não depende
de sorteios. Status representam a fotografia no último dia do cenário.
"""

import calendar
import re
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from random import Random

from faker import Faker

TABLE_DATES = {
    "clientes": "cadastrado_em",
    "contratos": "inicio",
    "pedidos": "data_pedido",
    "faturamento": "emissao",
    "indicadores_operacionais": "competencia",
}
STATUSES = {
    "contratos": {"ativo", "concluido", "cancelado"},
    "pedidos": {"aprovado", "entregue", "cancelado"},
    "faturamento": {"paga", "aberta", "cancelada"},
}
SUSTENTACAO_DESCRIPTIONS = (
    "Serviço de sustentação",
    "Ciclo de sustentação mensal",
    "Pacote de horas de consultoria",
    "Revisão e suporte mensal",
)
PROJETO_DESCRIPTIONS = (
    "Marco de projeto",
    "Entrega de incremento do projeto",
    "Sprint de desenvolvimento",
)
SUSTENTACAO_CONTRACT_DESCRIPTIONS = (
    "Sustentação mensal de aplicações",
    "Suporte contínuo de sistemas",
    "Manutenção evolutiva de aplicações",
)
PROJETO_CONTRACT_DESCRIPTIONS = (
    "Projeto de melhoria e integração",
    "Projeto de modernização de plataforma",
    "Projeto de integração de sistemas",
)


def month_range(start: str, end: str) -> list[date]:
    try:
        if not all(re.fullmatch(r"\d{4}-\d{2}", value) for value in (start, end)):
            raise ValueError
        first, last = date.fromisoformat(start + "-01"), date.fromisoformat(end + "-01")
        count = (last.year - first.year) * 12 + last.month - first.month + 1
        if not 1 <= count <= 24 or last.year >= 9999:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("Informe um período de um a 24 meses no formato AAAA-MM.") from None
    return [
        date(
            (first.year * 12 + first.month - 1 + n) // 12,
            (first.year * 12 + first.month - 1 + n) % 12 + 1,
            1,
        )
        for n in range(count)
    ]


def month_end(month: date) -> date:
    return month.replace(day=calendar.monthrange(month.year, month.month)[1])


def generate_comparative_data(
    seed: int, clients: int, start: str, end: str, *, version: str = "v1"
) -> dict:
    if version not in ("v1", "v2"):
        raise ValueError("Versão desconhecida. Use v1 ou v2.")
    months = month_range(start, end)
    if not 12 + len(months) <= clients <= 1000:
        raise ValueError(
            f"O perfil comparativo exige entre {12 + len(months)} e mil clientes "
            "para garantir cadastros mensais e a carteira inicial."
        )
    cutoff = month_end(months[-1])
    fake, rng = Faker("pt_BR"), Random(seed)
    fake.seed_instance(seed)
    data = {name: [] for name in TABLE_DATES}
    cities = [
        ("Joinville", "SC"),
        ("Blumenau", "SC"),
        ("Curitiba", "PR"),
        ("Florianópolis", "SC"),
        ("São Paulo", "SP"),
        ("Porto Alegre", "RS"),
    ]
    segments = ["Indústria", "Tecnologia", "Logística", "Serviços"]
    # Fatores declarados de cenário, não estimativas de desempenho de uma empresa.
    seasonality = [90, 94, 100, 103, 98, 106, 101, 110, 108, 114, 120, 92]

    def add_activity(contract, active_months, base_cents, project=False):
        contract["valor_contratado"] = Decimal("0.00")
        for month in active_months:
            index = months.index(month)
            factor = seasonality[month.month - 1] * (100 + 12 * (month.year - months[0].year))
            total_cents = base_cents * factor * rng.randint(92, 108) // 1_000_000
            # Entregas de tamanhos diferentes ao longo do mês, sem perder centavos.
            parts = [total_cents * 40 // 100, total_cents * 35 // 100]
            parts.append(total_cents - sum(parts))
            for slot, amount in enumerate(parts):
                order_id = len(data["pedidos"]) + 1
                code = (order_id + index) % 10
                status = "cancelado" if code == 0 else "aprovado" if code == 1 else "entregue"
                if version == "v2":
                    days_in_month = calendar.monthrange(month.year, month.month)[1]
                    window = days_in_month // len(parts)
                    ordered = month.replace(day=min(1 + slot * window + rng.randrange(window), days_in_month))
                    descricao = rng.choice(PROJETO_DESCRIPTIONS if project else SUSTENTACAO_DESCRIPTIONS)
                else:
                    ordered = month.replace(day=2 + slot * 7 + rng.randrange(3))
                    descricao = "Marco de projeto" if project else "Serviço de sustentação"
                value = Decimal(amount) / 100
                contract["valor_contratado"] += value
                data["pedidos"].append(
                    dict(
                        id=order_id,
                        contrato_id=contract["id"],
                        descricao=descricao,
                        data_pedido=ordered,
                        valor=value,
                        status=status,
                    )
                )
                if status != "cancelado":
                    # Parte da carteira tem faturamento parcelado para exercitar joins.
                    amounts = [amount] if order_id % 4 else [amount // 2, amount - amount // 2]
                    for part, invoice_amount in enumerate(amounts):
                        invoice_id = len(data["faturamento"]) + 1
                        emitted = ordered + timedelta(days=2 + part)
                        kind = (invoice_id + index) % 12
                        invoice_status = (
                            "cancelada"
                            if kind == 0
                            else ("aberta" if kind in (1, 2) or status == "aprovado" else "paga")
                        )
                        payment = min(emitted + timedelta(days=rng.randint(3, 22)), cutoff)
                        data["faturamento"].append(
                            dict(
                                id=invoice_id,
                                pedido_id=order_id,
                                numero_documento=f"COMP-{invoice_id:07d}",
                                emissao=emitted,
                                vencimento=emitted + timedelta(days=30),
                                pagamento=payment if invoice_status == "paga" else None,
                                valor=Decimal(invoice_amount) / 100,
                                status=invoice_status,
                            )
                        )
            planned = rng.randint(30, 80) if project else rng.randint(80, 200)
            opened = 0 if (contract["id"] + index) % 17 == 0 else rng.randint(5, 65)
            rate = min(98, 72 + (month.year - months[0].year) * 8 + rng.randrange(16))
            data["indicadores_operacionais"].append(
                dict(
                    id=len(data["indicadores_operacionais"]) + 1,
                    contrato_id=contract["id"],
                    competencia=month,
                    horas_previstas=Decimal(planned),
                    horas_realizadas=Decimal(planned * rng.randint(75, 130)) / 100,
                    chamados_abertos=opened,
                    chamados_resolvidos=opened * rate // 100,
                )
            )

    for client_id in range(1, clients + 1):
        registered = (
            (months[0] - timedelta(days=rng.randint(60, 300)))
            if client_id <= 12
            else (months[(client_id - 13) % len(months)])
        )
        city, state = cities[(client_id - 1) % len(cities)]
        data["clientes"].append(
            dict(
                id=client_id,
                nome=f"Empresa Fictícia {client_id:03d} {fake.company()}",
                segmento=segments[(client_id - 1) % len(segments)],
                cidade=city,
                uf=state,
                cadastrado_em=registered,
            )
        )
        eligible = [m for m in months if m >= registered]
        if client_id <= 12:
            eligible = months
        status = ["ativo", "concluido", "cancelado"][(client_id - 1) % 3]
        if status == "cancelado" and client_id > 12:
            eligible = eligible[: rng.randint(1, len(eligible))]
        contract = dict(
            id=len(data["contratos"]) + 1,
            cliente_id=client_id,
            descricao=(
                rng.choice(SUSTENTACAO_CONTRACT_DESCRIPTIONS)
                if version == "v2"
                else "Sustentação mensal de aplicações"
            ),
            modalidade="sustentacao",
            inicio=eligible[0],
            fim=date(cutoff.year + 1, 12, 31) if status == "ativo" else (month_end(eligible[-1])),
            status=status,
        )
        data["contratos"].append(contract)
        add_activity(contract, eligible, rng.randint(800_000, 4_000_000))
        # A carteira inicial garante novos projetos e todos os status em cada mês.
        project_months = months if client_id <= 12 else eligible[::3]
        for month in project_months:
            project_status = ["ativo", "concluido", "cancelado"][(client_id + month.month) % 3]
            project = dict(
                id=len(data["contratos"]) + 1,
                cliente_id=client_id,
                descricao=(
                    rng.choice(PROJETO_CONTRACT_DESCRIPTIONS)
                    if version == "v2"
                    else "Projeto de melhoria e integração"
                ),
                modalidade="projeto",
                inicio=month,
                fim=date(cutoff.year + 1, 12, 31)
                if project_status == "ativo"
                else (month_end(month)),
                status=project_status,
            )
            data["contratos"].append(project)
            add_activity(project, [month], rng.randint(200_000, 1_500_000), project=True)
    return data


def coverage_report(data: dict, start: str = "2025-01", end: str = "2026-10") -> dict:
    """Confere presença mensal e todos os status antes de publicar os totais."""
    months = month_range(start, end)
    monthly = []
    for month in months:
        finish = month_end(month)
        groups = {
            name: [r for r in data[name] if month <= r[field] <= finish]
            for name, field in TABLE_DATES.items()
        }
        for name, rows in groups.items():
            if not rows:
                raise ValueError(f"Cobertura ausente em {name}, competência {month:%Y-%m}.")
            if name in STATUSES and {r["status"] for r in rows} != STATUSES[name]:
                raise ValueError(f"Status incompletos em {name}, competência {month:%Y-%m}.")
        paid = [
            r
            for r in data["faturamento"]
            if r["pagamento"] is not None
            and month <= r["pagamento"] <= finish
            and r["status"] == "paga"
        ]
        if not paid:
            raise ValueError(f"Recebimentos ausentes em {month:%Y-%m}.")
        invoices = [r for r in groups["faturamento"] if r["status"] != "cancelada"]
        orders = [r for r in groups["pedidos"] if r["status"] != "cancelado"]
        indicators = groups["indicadores_operacionais"]

        def total(rows, field):
            # O schema usa escala 2; normaliza a representação sem alterar o valor.
            return format(sum((r[field] for r in rows), Decimal("0")), ".2f")

        monthly.append(
            {
                "mes": f"{month:%Y-%m}",
                "novos_clientes": len(groups["clientes"]),
                "contratos_iniciados": len(groups["contratos"]),
                "pedidos": len(orders),
                "valor_pedidos": total(orders, "valor"),
                "faturamento_emitido": total(invoices, "valor"),
                "recebimentos": total(paid, "valor"),
                "horas_previstas": total(indicators, "horas_previstas"),
                "horas_realizadas": total(indicators, "horas_realizadas"),
                "chamados_abertos": sum(r["chamados_abertos"] for r in indicators),
                "chamados_resolvidos": sum(r["chamados_resolvidos"] for r in indicators),
                "status": {
                    name: dict(Counter(r["status"] for r in groups[name])) for name in STATUSES
                },
            }
        )
    return {
        "perfil": "comparativo-v1",
        "inicio": start,
        "fim": end,
        "meses": len(months),
        "fotografia_status": str(month_end(months[-1])),
        "cenario_sintetico": True,
        "contagens": {k: len(v) for k, v in data.items()},
        "mensal": monthly,
    }
