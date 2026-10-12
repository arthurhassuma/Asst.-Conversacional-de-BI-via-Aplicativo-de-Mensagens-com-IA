import pytest

from app.managerial_queries import managerial_query
from app.managerial_rendering import render_managerial
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
    assert "2026-12-01" in text
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
