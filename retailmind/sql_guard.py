from __future__ import annotations

import re
from dataclasses import dataclass

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from retailmind.database import ALLOWED_TABLES


class UnsafeSQLError(ValueError):
    """Raised when generated SQL violates the read-only policy."""


@dataclass(frozen=True)
class SQLAudit:
    sql: str
    tables: tuple[str, ...]
    joins: int
    ctes: int
    checks: tuple[str, ...]


FORBIDDEN_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
    exp.Merge,
    exp.Transaction,
)


def validate_sql(
    sql: str,
    *,
    allowed_tables: frozenset[str] = ALLOWED_TABLES,
    max_length: int = 8_000,
    max_joins: int = 8,
    max_ctes: int = 6,
) -> SQLAudit:
    if not sql or not sql.strip():
        raise UnsafeSQLError("模型没有生成 SQL。")
    if len(sql) > max_length:
        raise UnsafeSQLError("SQL 过长，已拒绝执行。")
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise UnsafeSQLError("SQL 注释可能隐藏额外指令，已拒绝执行。")
    if re.search(r"\bWITH\s+RECURSIVE\b", sql, flags=re.IGNORECASE):
        raise UnsafeSQLError("不允许递归 CTE。")

    try:
        statements = parse(sql, read="sqlite")
    except ParseError as exc:
        raise UnsafeSQLError(f"SQL 语法无法解析：{exc}") from exc
    if len(statements) != 1:
        raise UnsafeSQLError("仅允许执行单条查询语句。")

    statement = statements[0]
    if not isinstance(statement, exp.Query):
        raise UnsafeSQLError("仅允许 SELECT / WITH ... SELECT 只读查询。")
    if any(statement.find(node_type) is not None for node_type in FORBIDDEN_NODES):
        raise UnsafeSQLError("检测到写入或管理型 SQL 指令。")

    cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}
    referenced = {
        table.name.lower()
        for table in statement.find_all(exp.Table)
        if table.name and table.name.lower() not in cte_names
    }
    unknown = referenced - allowed_tables
    if unknown:
        raise UnsafeSQLError(f"查询引用了未授权数据表：{', '.join(sorted(unknown))}")
    if not referenced:
        raise UnsafeSQLError("查询必须至少引用一个业务数据表。")

    joins = sum(1 for _ in statement.find_all(exp.Join))
    ctes = sum(1 for _ in statement.find_all(exp.CTE))
    if joins > max_joins:
        raise UnsafeSQLError(f"JOIN 数量超过限制（{joins} > {max_joins}）。")
    if ctes > max_ctes:
        raise UnsafeSQLError(f"CTE 数量超过限制（{ctes} > {max_ctes}）。")

    normalized = statement.sql(dialect="sqlite", pretty=True)
    return SQLAudit(
        sql=normalized,
        tables=tuple(sorted(referenced)),
        joins=joins,
        ctes=ctes,
        checks=(
            "单语句 AST 校验通过",
            "仅包含只读查询节点",
            "数据表白名单校验通过",
            "JOIN / CTE 复杂度在限制内",
            "SQLite 只读连接与执行资源限制已启用",
        ),
    )
