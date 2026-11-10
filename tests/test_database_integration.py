import os
from datetime import date
from decimal import Decimal

import psycopg
import pytest

from app.config import Settings
from app.database_tools import DatabaseTools
from app.query_templates import total_query
from scripts.manage_db import validate_data

pytestmark = pytest.mark.integration


@pytest.fixture
def settings():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Configure TEST_DATABASE_URL para executar com PostgreSQL real.")
    return Settings(
        _env_file=None, database_url=dsn.replace("@localhost:", "@127.0.0.1:"), max_query_rows=3
    )


def test_schema_and_exact_decimals(settings):
    db = DatabaseTools(settings)
    schema = db.get_schema()
    assert set(schema["tables"]) == {
        "clientes",
        "contratos",
        "pedidos",
        "faturamento",
        "indicadores_operacionais",
    }
    result = db.execute_sql("SELECT 123456789.123456::numeric AS total FROM clientes LIMIT 1")
    assert result["rows"] == [["123456789.123456"]]


def test_schema_lists_the_stored_spelling_of_categorical_values(settings):
    # Reservado do perfil autopecas (T04): a pergunta dizia "sustentação" e o dado guarda
    # "sustentacao"; sem ver a grafia real, o modelo copiou a da pergunta e contou zero contratos.
    # Os valores esperados vêm do próprio banco, porque cada perfil guarda um subconjunto diferente.
    db = DatabaseTools(settings)
    valores = db.get_schema()["valores"]
    for key in ("contratos.modalidade", "contratos.status", "pedidos.status", "faturamento.status"):
        table, column = key.split(".")
        stored = db.execute_sql(f"SELECT DISTINCT {column} FROM {table} ORDER BY 1")["rows"]
        assert valores[key] == [row[0] for row in stored], key
    assert set(valores["contratos.modalidade"]) <= {"projeto", "sustentacao"}
    assert valores["contratos.modalidade"], "o perfil precisa ter ao menos uma modalidade"
    assert "clientes.nome" not in valores and "contratos.descricao" not in valores


def test_server_row_limit(settings):
    result = DatabaseTools(settings).execute_sql("SELECT id FROM pedidos ORDER BY id LIMIT 9999")
    assert result["rows"] == [[1], [2], [3]]
    assert result["truncated"] is True


def test_server_timeout_and_recovery(settings):
    settings.query_timeout_ms = 50
    db = DatabaseTools(settings)
    result = db.execute_sql(
        "SELECT count(*) FROM pedidos a CROSS JOIN pedidos b CROSS JOIN pedidos c"
    )
    assert result["sqlstate"] == "57014"
    assert db.execute_sql("SELECT count(*) AS total FROM clientes")["rows"][0][0] > 0


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO clientes VALUES (99999, 'Teste', 'Teste', 'Teste', 'SC', CURRENT_DATE)",
        "UPDATE clientes SET nome='Alterado' WHERE id=1",
        "DELETE FROM clientes WHERE id=1",
        "CREATE TABLE public.proibida(id integer)",
        "CREATE TEMP TABLE proibida(id integer)",
    ],
)
def test_database_blocks_writes_without_application_validator(settings, statement):
    with psycopg.connect(settings.database_url.get_secret_value(), connect_timeout=5) as conn:
        conn.execute("SET TRANSACTION READ WRITE")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(statement)
        conn.rollback()


def test_synthetic_consistency_in_postgres(settings):
    with psycopg.connect(settings.database_url.get_secret_value(), connect_timeout=5) as conn:
        assert all(value == 0 for value in validate_data(conn).values())


def test_database_error_is_available_for_correction(settings):
    result = DatabaseTools(settings).execute_sql("SELECT inexistente FROM clientes")
    assert result["sqlstate"] == "42703"
    assert "inexistente" in result["database_detail"]


def test_percent_operator_and_like_patterns(settings):
    result = DatabaseTools(settings).execute_sql(
        "SELECT id % 2 AS total FROM clientes WHERE nome LIKE '%Empresa%' ORDER BY id LIMIT 1"
    )
    assert result["rows"] == [[1]]


def test_interval_result_is_exact_serializable_and_not_a_crash(settings):
    result = DatabaseTools(settings).execute_sql(
        "SELECT INTERVAL '1 day 01:02:03.123456' AS prazo FROM clientes LIMIT 1"
    )
    assert result["rows"] == [["1 dia, 1:02:03.123456"]]


@pytest.mark.parametrize(
    ("metric", "measure"),
    [
        ("recebimentos", "valor"),
        ("horas", "horas_realizadas"),
        ("chamados", "taxa_resolucao"),
    ],
)
def test_simple_total_business_rules_against_independent_rows(settings, metric, measure):
    start, end = date(2025, 8, 1), date(2025, 9, 1)
    with psycopg.connect(settings.database_url.get_secret_value()) as conn:
        if metric == "recebimentos":
            rows = conn.execute("SELECT pagamento, status, valor FROM faturamento").fetchall()
            values = [
                value
                for paid, status, value in rows
                if status == "paga" and paid is not None and start <= paid < end
            ]
            expected, count = sum(values), len(values)
        else:
            rows = conn.execute(
                "SELECT competencia, horas_realizadas, chamados_abertos, "
                "chamados_resolvidos FROM indicadores_operacionais"
            ).fetchall()
            selected = [row for row in rows if start <= row[0] < end]
            count = len(selected)
            if metric == "horas":
                expected = sum(row[1] for row in selected)
            else:
                # O total devolve pontos percentuais (85,71), não a razão (0,8571).
                expected = (
                    Decimal(sum(row[3] for row in selected)) * 100 / sum(row[2] for row in selected)
                )
    result = DatabaseTools(settings).execute_sql(
        total_query(
            {
                "metric": metric,
                "measure": measure,
                "period": {"start": start.isoformat(), "end": end.isoformat()},
            }
        )
    )
    assert "error" not in result
    assert result["rows"][0][1] == count > 0
    assert abs(Decimal(result["rows"][0][0]) - expected) < Decimal("1e-14")
