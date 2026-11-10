"""Conexões descartáveis, role de leitura e consultas limitadas no servidor."""

import json
import logging
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from time import monotonic

import psycopg
from psycopg import sql as pgsql

from app.config import Settings
from app.sql_policy import TABLES, UnsafeQuery, validate_select

logger = logging.getLogger(__name__)

CATEGORICAL_COLUMNS = {"modalidade", "status", "segmento", "uf"}
MAX_CATEGORICAL_VALUES = 30


def scalar(value):
    if isinstance(value, Decimal):
        return format(value, "f")  # Preserva dígitos e escala, inclusive zero; nunca float.
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value).replace("days", "dias").replace("day", "dia")
    return value


class DatabaseTools:
    def __init__(self, settings: Settings):
        self.settings = settings

    @contextmanager
    def connection(self):
        dsn = self.settings.database_url.get_secret_value()
        if not dsn:
            raise ValueError("Configure DATABASE_URL com o login readonly_agent.")
        with psycopg.connect(
            dsn, connect_timeout=5, options="-c search_path=pg_catalog,public"
        ) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                (str(self.settings.query_timeout_ms),),
            )
            conn.execute(
                "SELECT set_config('lock_timeout', %s, true)",
                (str(min(1000, self.settings.query_timeout_ms)),),
            )
            role = conn.execute("""SELECT current_user, rolsuper, rolcreaterole,
                rolcreatedb, rolreplication, rolbypassrls,
                EXISTS (SELECT 1 FROM pg_auth_members WHERE member = r.oid)
                FROM pg_roles r WHERE rolname = current_user""").fetchone()
            if not role or role[0] != "readonly_agent" or any(role[1:]):
                raise ValueError(
                    "A conexão deve usar exclusivamente a role readonly_agent restrita."
                )
            # Também recusa grants de escrita introduzidos acidentalmente depois do setup.
            bad = conn.execute("""SELECT EXISTS (SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
                AND has_table_privilege(current_user, c.oid,
                    'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'))
                OR has_schema_privilege(current_user, 'public', 'CREATE')""").fetchone()[0]
            if bad:
                raise ValueError("A role de leitura possui permissões de escrita indevidas.")
            yield conn

    @staticmethod
    def _categorical_values(conn, columns) -> dict:
        """Valores distintos das colunas de categoria, para o modelo filtrar com a grafia do dado.

        Só colunas de texto com nome de categoria e poucos valores distintos; nomes, descrições e
        outros textos livres não entram.
        """
        valores = {}
        for table, column, dtype, _ in columns:
            if column not in CATEGORICAL_COLUMNS or dtype not in ("character varying", "character"):
                continue
            found = conn.execute(
                pgsql.SQL(
                    "SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL ORDER BY 1 LIMIT %s"
                ).format(col=pgsql.Identifier(column), table=pgsql.Identifier(table)),
                (MAX_CATEGORICAL_VALUES + 1,),
            ).fetchall()
            if 0 < len(found) <= MAX_CATEGORICAL_VALUES:
                valores[f"{table}.{column}"] = [str(row[0]).strip() for row in found]
        return valores

    def get_schema(self) -> dict:
        try:
            with self.connection() as conn:
                rows = conn.execute(
                    """SELECT table_name, column_name, data_type, is_nullable
                    FROM information_schema.columns WHERE table_schema='public'
                    AND table_name = ANY(%s) ORDER BY table_name, ordinal_position LIMIT 100""",
                    (sorted(TABLES),),
                ).fetchall()
                valores = self._categorical_values(conn, rows)
            tables = {table: [] for table in sorted(TABLES)}
            for table, column, dtype, nullable in rows:
                tables[table].append(
                    {"column": column, "type": dtype, "nullable": nullable == "YES"}
                )
            return {
                "tables": tables,
                "valores": valores,
                "relationships": [
                    "contratos.cliente_id -> clientes.id",
                    "pedidos.contrato_id -> contratos.id",
                    "faturamento.pedido_id -> pedidos.id",
                    "indicadores_operacionais.contrato_id -> contratos.id",
                ],
                "definitions": "Em colunas de categoria, filtre pelos valores exatos listados em "
                "valores, com a mesma grafia e acentuação do dado, mesmo que a pergunta use outra. "
                "Faturamento: soma valor por emissao, exceto cancelada. "
                "Recebimentos: soma valor por pagamento, somente paga. "
                "Pedidos: soma valor por data_pedido, exceto cancelado. "
                "Contratos: valor_contratado; não somar após joins multiplicadores. "
                "Competência operacional mensal; taxa = soma resolvidos / soma abertos. "
                "Domínio: revenda de autopeças que vende a oficinas, frotas e lojas. "
                "Pedidos são pedidos de venda de peças; contratos são contratos de fornecimento "
                "(sustentacao = reposição recorrente, projeto = fornecimento pontual); "
                "faturamento são notas fiscais; horas_previstas/horas_realizadas são horas de "
                "atendimento; chamados_abertos/chamados_resolvidos são ocorrências de pós-venda "
                "(garantias, trocas e devoluções). "
                "Moeda BRL. Todas as datas e empresas são sintéticas.",
            }
        except (psycopg.Error, ValueError):
            return {
                "error": "Não foi possível consultar o esquema. Verifique a configuração do banco."
            }

    def execute_sql(self, sql: str) -> dict:
        started = monotonic()
        try:
            query = validate_select(sql)
            with self.connection() as conn:
                # LIMIT fora da consulta também limita SELECTs sem LIMIT ou com LIMIT maior.
                with conn.cursor() as cur:
                    # O único valor interpolado além da AST normalizada é um inteiro
                    # validado. Sem bind parameters, '%' do SQL não vira placeholder.
                    cur.execute(
                        f"SELECT * FROM ({query}) AS resultado LIMIT {self.settings.max_query_rows + 1}"
                    )
                    columns = [c.name for c in cur.description]
                    rows = cur.fetchall()
            truncated = len(rows) > self.settings.max_query_rows
            rows = [[scalar(v) for v in row] for row in rows[: self.settings.max_query_rows]]
            result = {"columns": columns, "rows": rows, "truncated": truncated}
            if len(json.dumps(result, ensure_ascii=False)) > 60000:
                return {"error": "Resultado muito extenso. Agregue os dados ou reduza as colunas."}
            logger.info(
                "consulta_concluida duracao_ms=%d linhas=%d parcial=%s",
                int((monotonic() - started) * 1000),
                len(rows),
                truncated,
            )
            return result
        except UnsafeQuery as exc:
            return {"error": str(exc)}
        except psycopg.errors.QueryCanceled:
            return {
                "error": "A consulta excedeu o tempo permitido. Simplifique os filtros ou agregações.",
                "sqlstate": "57014",
            }
        except psycopg.Error as exc:
            # Diagnóstico do servidor é dado interno para autocorreção, nunca resposta ao gestor.
            detail = (exc.diag.message_primary or "")[:500]
            return {
                "error": "O banco recusou a consulta. Corrija o SQL e tente novamente.",
                "sqlstate": exc.sqlstate,
                "database_detail": detail,
            }
        except ValueError:
            return {
                "error": "Configuração de acesso ao banco inválida. Use a role somente leitura."
            }
