import pytest

from app.sql_policy import UnsafeQuery, validate_select


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT count(*) AS total FROM clientes",
        "SELECT sum(valor) AS total FROM faturamento WHERE status <> 'cancelada'",
        "WITH x AS (SELECT id FROM clientes) SELECT count(*) FROM x",
        "SELECT date_trunc('month', emissao), sum(valor) FROM faturamento GROUP BY 1",
        "SELECT c.nome, sum(p.valor) FROM clientes c JOIN contratos ct ON ct.cliente_id=c.id JOIN pedidos p ON p.contrato_id=ct.id GROUP BY c.nome",
        "SELECT round(avg(horas_realizadas), 2) FROM indicadores_operacionais",
    ],
)
def test_accepts_analytical_select(sql):
    assert validate_select(sql).startswith(("SELECT", "WITH"))


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM clientes",
        "SELECT 1; DROP TABLE clientes",
        "WITH x AS (DELETE FROM clientes RETURNING *) SELECT * FROM x",
        "SELECT * INTO copia FROM clientes",
        "SELECT * FROM clientes FOR UPDATE",
        "SELECT pg_sleep(10)",
        "SELECT set_config('transaction_read_only','off',true)",
        "SELECT * FROM pg_catalog.pg_authid",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM outro.clientes",
        "SELECT public.sum(valor) FROM pedidos",
        "SELECT * FROM generate_series(1, 100000000)",
        "WITH RECURSIVE x AS (SELECT 1 UNION ALL SELECT 1 FROM x) SELECT * FROM x",
        "EXPLAIN SELECT * FROM clientes",
        "COPY clientes TO STDOUT",
        "SELECT lo_import('arquivo')",
        "SELECT current_user",
        "SELECT 'x'::regclass",
        "SELECT 1 OPERATOR(public.+) 1",
        "",
    ],
)
def test_rejects_unsafe_sql(sql):
    with pytest.raises(UnsafeQuery):
        validate_select(sql)


def test_cte_in_subquery_does_not_authorize_outer_table():
    with pytest.raises(UnsafeQuery):
        validate_select(
            "SELECT * FROM segredo, (WITH segredo AS (SELECT 1) SELECT * FROM segredo) x"
        )
