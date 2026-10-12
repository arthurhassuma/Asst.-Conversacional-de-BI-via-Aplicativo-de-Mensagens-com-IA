import pytest

from app.managerial_queries import managerial_query
from app.managerial_rendering import render_managerial
from app.messaging import message_chunks
from app.rendering import InvalidAnswer, cell_text
from tests.test_analysis_contract import PLAN


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
