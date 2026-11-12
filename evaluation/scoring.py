from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def normalize_cell(value, kind):
    if value is None:
        return ("null",)
    if kind == "number":
        if isinstance(value, (bool, float)):
            raise ValueError("Número impreciso ou booleano.")
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError("Número não finito.")
        return ("number", number)
    if kind == "text":
        if not isinstance(value, str):
            raise ValueError("Texto esperado.")
        return ("text", value)
    if kind == "date":
        if isinstance(value, datetime):
            if value.time().isoformat() != "00:00:00":
                raise ValueError("Data com horário inesperado.")
            value = value.date()
        if isinstance(value, date):
            return ("date", value.isoformat())
        return ("date", date.fromisoformat(value).isoformat())
    raise ValueError("Tipo de referência desconhecido.")


def compare_rows(actual, expected, kinds, *, ordered):
    def normalized(rows):
        return [
            tuple(normalize_cell(v, kind) for v, kind in zip(row, kinds, strict=True))
            for row in rows
        ]

    try:
        observed, reference = normalized(actual), normalized(expected)
    except (ValueError, TypeError, InvalidOperation):
        return False
    return observed == reference if ordered else Counter(observed) == Counter(reference)
