"""Setup explícito com credencial administrativa; nunca chamado por tools do agente."""

import json
from pathlib import Path

import psycopg
from psycopg import sql

from app.cli_support import PortugueseArgumentParser
from app.config import Settings
from scripts.autopecas_seed import PROFILE as AUTOPECAS_PROFILE
from scripts.autopecas_seed import REQUIRED_STATUSES as AUTOPECAS_STATUSES
from scripts.comparative_seed import TABLE_DATES, coverage_report
from scripts.seed import day_coverage_report, generate_data

ROOT = Path(__file__).resolve().parents[1]


def initialize(conn, password: str):
    if not password or password.startswith("troque_"):
        raise ValueError("Configure uma READONLY_PASSWORD própria antes de inicializar.")
    if conn.execute("SELECT to_regclass('public.clientes')").fetchone()[0]:
        raise ValueError("O schema já existe; inicialização recusada para preservar dados.")
    conn.execute((ROOT / "db/schema.sql").read_text(encoding="utf-8"))
    if conn.execute("SELECT 1 FROM pg_roles WHERE rolname='readonly_agent'").fetchone():
        raise ValueError("A role readonly_agent já existe neste cluster. Use um cluster dedicado.")
    conn.execute(
        sql.SQL("CREATE ROLE readonly_agent LOGIN PASSWORD {}").format(sql.Literal(password))
    )
    conn.execute((ROOT / "db/roles.sql").read_text(encoding="utf-8"))
    db = conn.execute("SELECT current_database()").fetchone()[0]
    conn.execute(
        sql.SQL("REVOKE CREATE, TEMPORARY ON DATABASE {} FROM PUBLIC").format(sql.Identifier(db))
    )
    conn.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO readonly_agent").format(sql.Identifier(db))
    )


def initialize_state(conn, password: str):
    """Cria (ou atualiza, de forma idempotente) o schema `estado` e a role app_estado.

    Não toca nas tabelas de negócio nem na role de leitura; pode rodar em base já populada.
    """
    if not password or password.startswith("troque_"):
        raise ValueError("Configure uma STATE_PASSWORD própria antes de inicializar o estado.")
    if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='app_estado'").fetchone():
        conn.execute(
            sql.SQL("CREATE ROLE app_estado LOGIN PASSWORD {}").format(sql.Literal(password))
        )
    conn.execute(
        "ALTER ROLE app_estado NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS"
    )
    conn.execute("ALTER ROLE app_estado SET search_path = pg_catalog")
    conn.execute((ROOT / "db/estado.sql").read_text(encoding="utf-8"))
    db = conn.execute("SELECT current_database()").fetchone()[0]
    conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO app_estado").format(sql.Identifier(db)))


def seed_database(
    conn,
    seed: int = 42,
    clients: int = 30,
    *,
    profile: str = "original",
    start_month: str = "2025-01",
    end_month: str = "2026-10",
):
    if conn.execute("SELECT EXISTS(SELECT 1 FROM clientes)").fetchone()[0]:
        raise ValueError("A base já contém clientes; a carga foi recusada para preservar dados.")
    data = generate_data(
        seed, clients, profile=profile, start_month=start_month, end_month=end_month
    )
    if profile in ("comparativo", "comparativo-v2"):
        coverage_report(data, start_month, end_month)
    if profile == "autopecas":
        coverage_report(
            data, start_month, end_month, required=AUTOPECAS_STATUSES, profile=AUTOPECAS_PROFILE
        )
    if profile in ("original-v2", "comparativo-v2"):
        day_coverage_report(data)
    with conn.cursor() as cur:
        for table, rows in data.items():
            columns = list(rows[0])
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table),
                sql.SQL(",").join(map(sql.Identifier, columns)),
                sql.SQL(",").join(sql.Placeholder() for _ in columns),
            )
            cur.executemany(query, [[row[col] for col in columns] for row in rows])
    return {table: len(rows) for table, rows in data.items()}


def database_coverage(conn, start: str = "2025-01", end: str = "2026-10", profile: str = ""):
    """Auditoria administrativa da base comparativa, sem usar a API de IA."""
    from psycopg.rows import dict_row

    conn.execute("SET LOCAL statement_timeout = '8000ms'")
    data = {}
    with conn.cursor(row_factory=dict_row) as cur:
        for table in TABLE_DATES:
            cur.execute(sql.SQL("SELECT * FROM {} ORDER BY id").format(sql.Identifier(table)))
            data[table] = cur.fetchall()
    if profile == "autopecas":
        return coverage_report(
            data, start, end, required=AUTOPECAS_STATUSES, profile=AUTOPECAS_PROFILE
        )
    return coverage_report(data, start, end)


def validate_data(conn):
    checks = {
        "clientes_sem_contrato": """SELECT count(*) FROM clientes c WHERE NOT EXISTS
            (SELECT 1 FROM contratos ct WHERE ct.cliente_id=c.id)""",
        "pedidos_fora_do_contrato": """SELECT count(*) FROM pedidos p JOIN contratos c
            ON c.id=p.contrato_id WHERE p.data_pedido NOT BETWEEN c.inicio AND c.fim""",
        "faturamento_inconsistente": """SELECT count(*) FROM faturamento f JOIN pedidos p
            ON p.id=f.pedido_id WHERE f.emissao<p.data_pedido OR p.status='cancelado' """,
        "excesso_faturado": """SELECT count(*) FROM (SELECT p.id FROM pedidos p JOIN faturamento f
            ON f.pedido_id=p.id WHERE f.status<>'cancelada' GROUP BY p.id HAVING sum(f.valor)>p.valor) x""",
        "excesso_pedido": """SELECT count(*) FROM (SELECT c.id FROM contratos c JOIN pedidos p
            ON p.contrato_id=c.id WHERE p.status<>'cancelado' GROUP BY c.id
            HAVING sum(p.valor)>c.valor_contratado) x""",
        "competencias_fora_do_contrato": """SELECT count(*) FROM indicadores_operacionais i
            JOIN contratos c ON c.id=i.contrato_id
            WHERE i.competencia<c.inicio OR i.competencia>c.fim""",
    }
    errors = {name: conn.execute(query).fetchone()[0] for name, query in checks.items()}
    if any(errors.values()):
        raise ValueError(f"Falha na consistência: {errors}")
    return errors


def main():
    parser = PortugueseArgumentParser(description="Administração da base sintética de BI")
    parser.add_argument("command", choices=["init", "init-state", "seed", "validate", "coverage"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--clients",
        type=int,
        default=None,
        help="Padrão: 30 nos perfis original e original-v2; 100 nos demais.",
    )
    parser.add_argument(
        "--profile",
        choices=["original", "original-v2", "comparativo", "comparativo-v2", "autopecas"],
        default="original",
    )
    parser.add_argument("--start-month", default="2025-01")
    parser.add_argument("--end-month", default="2026-10")
    parser.add_argument("--env-file", default=".env", help="Arquivo local de configuração.")
    args = parser.parse_args()
    settings = Settings(_env_file=args.env_file)
    dsn = settings.admin_database_url.get_secret_value()
    if not dsn:
        parser.exit(1, "Configure ADMIN_DATABASE_URL no arquivo .env.\n")
    try:
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            if args.command == "init":
                initialize(conn, settings.readonly_password.get_secret_value())
                result = {"status": "Schema e role somente leitura criados."}
            elif args.command == "init-state":
                initialize_state(conn, settings.state_password.get_secret_value())
                result = {"status": "Estado durável (schema estado e role app_estado) pronto."}
            elif args.command == "seed":
                clients = (
                    args.clients
                    if args.clients is not None
                    else (30 if args.profile in ("original", "original-v2") else 100)
                )
                result = seed_database(
                    conn,
                    args.seed,
                    clients,
                    profile=args.profile,
                    start_month=args.start_month,
                    end_month=args.end_month,
                )
                validate_data(conn)
            elif args.command == "coverage":
                conn.execute("SET TRANSACTION READ ONLY")
                validate_data(conn)
                result = database_coverage(conn, args.start_month, args.end_month, args.profile)
            else:
                result = validate_data(conn)
        print(json.dumps(result, ensure_ascii=False))
    except (psycopg.Error, ValueError) as exc:
        # Mensagens psycopg podem conter dados de conexão; não exibir DSN/segredos.
        message = (
            str(exc)
            if isinstance(exc, ValueError)
            else "Falha no banco. Verifique conexão, permissões e schema."
        )
        parser.exit(1, message + "\n")


if __name__ == "__main__":
    main()
