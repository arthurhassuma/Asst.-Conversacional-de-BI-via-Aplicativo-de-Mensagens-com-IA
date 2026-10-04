"""Allowlist sobre a AST real de PostgreSQL; falha fechada para sintaxe desconhecida."""

from pglast import Error, parse_sql
from pglast.stream import RawStream

TABLES = frozenset({"clientes", "contratos", "pedidos", "faturamento", "indicadores_operacionais"})
FUNCTIONS = frozenset(
    {
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "round",
        "abs",
        "ceil",
        "ceiling",
        "floor",
        "date_trunc",
        "date_part",
        "extract",
        "lower",
        "upper",
        "length",
        "btrim",
        "row_number",
        "rank",
        "dense_rank",
        "lag",
        "lead",
        "first_value",
        "last_value",
    }
)
NODES = frozenset(
    {
        "RawStmt",
        "SelectStmt",
        "ResTarget",
        "ColumnRef",
        "A_Star",
        "RangeVar",
        "Alias",
        "A_Const",
        "Integer",
        "Float",
        "String",
        "Boolean",
        "BitString",
        "A_Expr",
        "BoolExpr",
        "NullTest",
        "BooleanTest",
        "FuncCall",
        "TypeCast",
        "TypeName",
        "SortBy",
        "JoinExpr",
        "WithClause",
        "CommonTableExpr",
        "RangeSubselect",
        "SubLink",
        "CaseExpr",
        "CaseWhen",
        "CoalesceExpr",
        "MinMaxExpr",
        "WindowDef",
        "GroupingSet",
        "RowExpr",
        "List",
    }
)
TYPES = frozenset(
    {
        "date",
        "timestamp",
        "timestamptz",
        "interval",
        "numeric",
        "decimal",
        "int2",
        "int4",
        "int8",
        "integer",
        "bigint",
        "text",
        "varchar",
        "bool",
    }
)


class UnsafeQuery(ValueError):
    pass


def walk(value):
    if isinstance(value, dict):
        if "@" in value:
            yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from walk(child)


def validate_relations(value, visible_ctes=frozenset()):
    """CTE autoriza referências só dentro do seu escopo lexical, nunca em irmãos."""
    if isinstance(value, dict):
        if value.get("@") == "SelectStmt":
            clause = value.get("withClause") or {}
            visible_ctes = visible_ctes | {cte["ctename"] for cte in clause.get("ctes") or []}
        if value.get("@") == "RangeVar":
            schema = value.get("schemaname")
            allowed = TABLES if schema else TABLES | visible_ctes
            if (
                value.get("catalogname")
                or schema not in (None, "public")
                or value["relname"] not in allowed
            ):
                raise UnsafeQuery(
                    "Somente as tabelas de negócio autorizadas podem ser consultadas."
                )
        for child in value.values():
            validate_relations(child, visible_ctes)
    elif isinstance(value, (list, tuple)):
        for child in value:
            validate_relations(child, visible_ctes)


def validate_select(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 12000:
        raise UnsafeQuery("Consulta vazia ou acima do tamanho permitido.")
    try:
        statements = parse_sql(sql)
    except (Error, RecursionError) as exc:
        raise UnsafeQuery("Sintaxe SQL inválida. Revise a consulta SELECT.") from exc
    if len(statements) != 1 or type(statements[0].stmt).__name__ != "SelectStmt":
        raise UnsafeQuery("Somente uma consulta SELECT é permitida.")
    nodes = list(walk(statements[0]()))
    if len(nodes) > 2000:
        raise UnsafeQuery("Consulta complexa demais para este assistente.")
    validate_relations(statements[0]())
    for node in nodes:
        kind = node["@"]
        if kind not in NODES:
            raise UnsafeQuery("A consulta contém uma operação fora da lista permitida.")
        if kind == "SelectStmt" and (node.get("intoClause") or node.get("lockingClause")):
            raise UnsafeQuery("SELECT INTO e bloqueios explícitos não são permitidos.")
        if kind == "WithClause" and node.get("recursive"):
            raise UnsafeQuery("CTEs recursivas não são permitidas.")
        if kind == "FuncCall":
            name = [p["sval"] for p in node["funcname"]]
            if len(name) != 1 or name[0] not in FUNCTIONS:
                raise UnsafeQuery("Função SQL fora da lista permitida.")
        if kind == "TypeName":
            names = [p["sval"] for p in node["names"]]
            if (
                names[-1] not in TYPES
                or len(names) > 2
                or (len(names) == 2 and names[0] != "pg_catalog")
            ):
                raise UnsafeQuery("Conversão de tipo fora da lista permitida.")
        if kind == "A_Expr":
            names = [p["sval"] for p in node.get("name") or []]
            if len(names) != 1 or names[0] not in {
                "=",
                "<>",
                "!=",
                "<",
                ">",
                "<=",
                ">=",
                "+",
                "-",
                "*",
                "/",
                "%",
                "~~",
                "!~~",
                "~~*",
                "!~~*",
                "||",
            }:
                raise UnsafeQuery("Operador SQL fora da lista permitida.")
    return RawStream()(statements[0].stmt)
