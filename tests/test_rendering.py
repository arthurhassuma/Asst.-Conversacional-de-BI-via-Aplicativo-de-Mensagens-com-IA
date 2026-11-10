import pytest

from app.rendering import InvalidAnswer, render_answer


def test_numbers_are_rendered_exactly_from_query_not_model_prose():
    results = {"q1": {"columns": ["total"], "rows": [["123456789.123456"]], "truncated": False}}
    text = render_answer({"kind": "answer", "result_id": "q1"}, results, "faturamento")
    assert "123.456.789,123456" in text
    assert "123.456.789,12\n" not in text


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
    assert "Não encontrei registros" in text
    assert "0" not in text


@pytest.mark.parametrize(
    ("metric", "measure", "value", "expected"),
    [
        (
            "faturamento",
            "valor",
            "123456789.123456",
            "📊 Resultado para faturamento emitido: 123.456.789,123456.",
        ),
        (
            "clientes",
            "quantidade",
            30,
            "📊 Resultado para quantidade de clientes: 30.",
        ),
        (
            "horas",
            "horas_realizadas",
            "0.00",
            "📊 Resultado para horas realizadas: 0,00.",
        ),
    ],
)
def test_scalar_answer_uses_natural_portuguese_and_exact_cell(metric, measure, value, expected):
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["total"], "rows": [[value]], "truncated": False}},
        metric,
        measure=measure,
    )
    assert text == expected


@pytest.mark.parametrize("value", [None, "valor desconhecido"])
def test_missing_or_textual_scalar_is_not_presented_as_money(value):
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["total"], "rows": [[value]], "truncated": False}},
        "faturamento",
        measure="valor",
    )
    assert "R$" not in text
    assert "0" not in text


def test_partial_scalar_still_has_warning_instead_of_claiming_total():
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["total"], "rows": [["12.3456"]], "truncated": True}},
        "faturamento",
        measure="valor",
    )
    assert "Resultado parcial" in text
    assert "12,3456" in text
    assert "foi de" not in text


@pytest.mark.parametrize(
    ("metric", "measure", "value"),
    [("horas", "horas_realizadas", "3.125"), ("faturamento", "valor", "12.345678")],
)
def test_alias_total_does_not_prove_sum_or_currency(metric, measure, value):
    # AVG(horas_realizadas) AS total e variação percentual AS total são
    # resultados possíveis: o alias não certifica a operação nem a unidade.
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["total"], "rows": [[value]], "truncated": False}},
        metric,
        measure=measure,
    )
    assert "somaram" not in text
    assert "R$" not in text
    assert value.replace(".", ",") in text


def test_generic_value_label_does_not_call_average_a_total():
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["media", "registros"], "rows": [["12.345", 2]], "truncated": False}},
        "pedidos",
        measure="valor",
    )
    assert "valor total" not in text
    assert "12,345" in text


def test_category_columns_have_fixed_labels_instead_of_the_generic_one():
    # Reavaliação no perfil autopecas: "clientes por UF" saía como "Campo: SC · Quantidade: 18".
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {
            "q1": {
                "columns": ["uf", "quantidade", "registros"],
                "rows": [["SC", 18, 18], ["PR", 3, 3]],
                "truncated": False,
            }
        },
        "clientes",
        {"start": "2023-01-01", "end": "2024-01-01"},
        "quantidade",
    )
    assert "UF: SC · Quantidade: 18" in text and "UF: PR · Quantidade: 3" in text
    assert "Campo:" not in text


@pytest.mark.parametrize(
    ("column", "label"),
    [("modalidade", "Modalidade"), ("segmento", "Segmento"), ("cidade", "Cidade")],
)
def test_other_category_columns_are_labeled(column, label):
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": [column, "total"], "rows": [["x", "10.00"]], "truncated": False}},
        "contratos",
        {"start": "2025-01-01", "end": "2026-01-01"},
        "valor",
    )
    assert f"{label}: x" in text and "Campo:" not in text


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
    assert ("Não encontrei registros" in text) is absent
    assert "01/09/2026 a 30/09/2026" in text
    assert "Campo:" not in text
    if absent:
        assert "não informado" not in text
    else:
        assert f"Valor: {'não informado' if total is None else total}" in text


def test_single_free_sql_value_is_one_labeled_line_without_repeating_the_measure():
    text = render_answer(
        {"kind": "answer", "result_id": "q1"},
        {"q1": {"columns": ["quantidade", "registros"], "rows": [[1, 1]], "truncated": False}},
        "clientes",
        {"start": "2026-10-01", "end": "2026-11-01"},
        "quantidade",
    )
    assert text.splitlines() == [
        "📊 Resultado de clientes",
        "Período: 01/10/2026 a 31/10/2026",
        "Quantidade: 1",
    ]
