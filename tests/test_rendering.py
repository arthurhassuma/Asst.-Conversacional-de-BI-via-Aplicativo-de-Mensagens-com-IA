import pytest

from app.rendering import InvalidAnswer, render_answer


def test_numbers_are_rendered_exactly_from_query_not_model_prose():
    results = {"q1": {"columns": ["total"], "rows": [["123456789.123456"]], "truncated": False}}
    text = render_answer({"kind": "answer", "result_id": "q1"}, results, "faturamento")
    assert "123456789,123456" in text
    assert "123456789,12\n" not in text


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "answer", "result_id": "q999"},
        {"kind": "answer", "result_id": "q1", "text": "Total de 999 reais"},
    ],
)
def test_rejects_unbacked_references_and_free_prose(payload):
    with pytest.raises(InvalidAnswer):
        render_answer(
            payload, {"q1": {"columns": ["n"], "rows": [[7]], "truncated": False}}, "pedidos"
        )


def test_numeric_alias_is_not_printed_and_empty_does_not_imply_zero():
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["total_999"], "rows": [], "truncated": False}},
        "pedidos",
    )
    assert "999" not in text
    assert "Nenhum registro" in text
    assert "0" not in text


@pytest.mark.parametrize(
    ("total", "count", "absent"), [(None, 0, True), (None, 2, False), ("0", 2, False)]
)
def test_aggregate_absence_requires_row_count_not_just_null_or_zero(total, count, absent):
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["total", "registros"], "rows": [[total, count]], "truncated": False}},
        "pedidos",
        {"start": "2026-09-01", "end": "2026-10-01"},
        "valor",
    )
    assert ("Nenhum registro" in text) is absent
    assert "01/09/2026 a 30/09/2026" in text
    assert "Campo:" not in text
    if absent:
        assert "não informado" not in text
    else:
        assert f"Total: {'não informado' if total is None else total}" in text
