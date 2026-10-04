import os

import psycopg
import pytest

from app.config import Settings
from app.database_tools import DatabaseTools
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
