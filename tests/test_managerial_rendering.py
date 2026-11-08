import pytest

from app.managerial_queries import managerial_query
from app.managerial_rendering import grouping_key, render_managerial, render_managerial_group
from app.messaging import message_chunks
from app.rendering import InvalidAnswer, cell_text, render_answer
from tests.test_analysis_contract import PLAN


@pytest.mark.parametrize("zero", ["0E-20", "0.00000000000000000000"])
def test_scaled_zero_remains_exact_in_stable_comparison(zero):
    from decimal import Decimal

    from app.database_tools import scalar

    result = {"columns": ["base", "atual", "diferenca", "variacao_percentual", "direcao", "registros"],
              "rows": [["100.00", "100.00", scalar(Decimal(zero)), scalar(Decimal(zero)), "ficou_estavel", 2]],
              "truncated": False}
    text = render_managerial(result, managerial_query(PLAN)["context"])
    assert "estável" in text and "0,00%" in text


def test_decimal_transport_never_uses_exponential_notation():
    from decimal import Decimal

    from app.database_tools import scalar
    assert scalar(Decimal("0E-20")) == "0.00000000000000000000"
    assert scalar(Decimal("1E+3")) == "1000"


def test_friendly_format_preserves_all_digits():
    assert cell_text("123456789.123456") == "123.456.789,123456"
    assert cell_text("-0.0010") == "-0,0010"


def test_comparison_has_friendly_text_and_only_cell_numbers():
    context = managerial_query(PLAN)["context"]
    result = {
        "columns": [
            "item",
            "base",
            "atual",
            "diferenca",
            "variacao_percentual",
            "direcao",
            "registros",
        ],
        "rows": [["Total", "1000.00", "1250.123456", "250.123456", None, "aumentou", 2]],
        "truncated": False,
    }
    text = render_managerial(result, context)
    assert "📊" in text and "📈" in text
    assert "1.250,123456" in text and "250,123456" in text
    assert "Sem base comparável" in text
    assert "inadimplência" not in text and "causa" not in text


def test_render_managerial_group_merges_same_header_once():
    period = {"start": "2025-01-01", "end": "2025-02-01", "evidence": "janeiro de 2025"}
    base_context = {
        "source": "controlled_template",
        "kind": "total",
        "metric": "pedidos",
        "period": period,
    }
    value_context = {**base_context, "measure": "valor", "unit": "BRL"}
    count_context = {**base_context, "measure": "quantidade", "unit": "quantidade"}
    value_result = {"columns": ["total"], "rows": [["1000.00"]], "truncated": False}
    count_result = {"columns": ["total"], "rows": [["7"]], "truncated": False}
    text = render_managerial_group([(value_result, value_context), (count_result, count_context)])
    assert text.count("Período:") == 1
    assert text.count("Resumo de pedidos de venda") == 1
    assert text.splitlines()[2:] == ["Valor: R$ 1.000,00", "Quantidade: 7 pedidos"]


def test_grouping_key_distinguishes_period_metric_and_kind():
    period_a = {"start": "2025-01-01", "end": "2025-02-01", "evidence": "janeiro de 2025"}
    period_b = {"start": "2025-02-01", "end": "2025-03-01", "evidence": "fevereiro de 2025"}
    base = {"metric": "pedidos", "kind": "total", "group_by": None, "period": period_a}
    assert grouping_key(base) == grouping_key({**base, "period": dict(period_a)})
    assert grouping_key(base) != grouping_key({**base, "period": period_b})
    assert grouping_key(base) != grouping_key({**base, "metric": "faturamento"})
    assert grouping_key(base) != grouping_key({**base, "kind": "comparacao"})


def test_untrusted_context_is_rejected():
    with pytest.raises(InvalidAnswer):
        render_managerial(
            {"rows": [[999]], "columns": ["total"], "truncated": False},
            {"source": "llm", "kind": "comparacao"},
        )


def test_long_detail_is_labeled_and_values_are_not_cut():
    context = managerial_query(PLAN)["context"]
    context.update(kind="ranking", group_by="cliente")
    rows = [[f"Empresa {i}", "123456789.123456"] for i in range(30)]
    text = render_managerial(
        {"columns": ["item", "valor"], "rows": rows, "truncated": True}, context
    )
    assert "parcial" in text.lower()
    chunks = message_chunks(text)
    assert all("123.456.789,123456" in c for c in chunks if "Valor:" in c)
    assert any("parcial" in c.lower() for c in chunks)


def test_monthly_series_keeps_every_month_when_it_fits():
    context = managerial_query(PLAN)["context"]
    context.update(kind="tendencia", group_by="mes")
    rows = [[f"2026-{i:02d}-01", "1200.00"] for i in range(1, 13)]
    text = render_managerial(
        {"columns": ["item", "valor"], "rows": rows, "truncated": False}, context
    )
    assert "Dezembro de 2026 — R$ 1.200,00" in text
    assert "primeiros registros" not in text


def test_free_sql_results_are_friendly_without_inventing_units():
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["total"], "rows": [["1234.56"]], "truncated": False}},
        "faturamento",
        measure="valor",
    )
    assert text.startswith("📊") and "1.234,56" in text
    assert "R$" not in text and "causa" not in text


def _context(**changes):
    period = {"start": "2026-10-01", "end": "2026-11-01", "evidence": "outubro de 2026"}
    base = {
        "source": "controlled_template",
        "kind": "ranking",
        "group_by": "cliente",
        "metric": "pedidos",
        "measure": "quantidade",
        "unit": "quantidade",
        "period": period,
    }
    return {**base, **changes}


def test_ranking_is_compact_numbered_and_hides_internal_ids():
    rows = [
        ["12 — Auto Mecânica Santa Cruz", "9", 9, 1],
        ["3 — Funilaria Carvalho", "1", 1, 2],
    ]
    text = render_managerial(
        {"columns": ["item", "valor", "registros", "posicao"], "rows": rows, "truncated": False},
        _context(),
    )
    lines = text.splitlines()
    assert "1. Auto Mecânica Santa Cruz — 9 pedidos" in lines
    assert "2. Funilaria Carvalho — 1 pedido" in lines
    assert "12 —" not in text and "Posição" not in text
    assert "" not in lines[3:-1]  # sem linhas em branco entre os itens


def test_contract_ranking_keeps_contract_number_after_the_name():
    text = render_managerial(
        {
            "columns": ["item", "valor", "registros", "posicao"],
            "rows": [["7 — Auto Elétrica Brasil", "4", 4, 1]],
            "truncated": False,
        },
        _context(group_by="contrato"),
    )
    assert "1. Auto Elétrica Brasil · contrato 7 — 4 pedidos" in text


def test_single_day_period_is_not_repeated_as_a_range():
    period = {"start": "2026-11-05", "end": "2026-11-06", "evidence": "ontem"}
    text = render_managerial(
        {"columns": ["quantidade", "registros"], "rows": [[None, 0]], "truncated": False},
        _context(kind="total", group_by=None, metric="clientes", period=period),
    )
    assert "Período: 05/11/2026\n" in text + "\n" and " a 05/11/2026" not in text


def test_total_lines_use_the_measure_label_once():
    result = {"columns": ["total", "registros"], "rows": [["2401621.96", 295]], "truncated": False}
    text = render_managerial(result, _context(kind="total", group_by=None, measure="valor", unit="BRL"))
    assert text.splitlines()[2:] == ["Valor: R$ 2.401.621,96"]
