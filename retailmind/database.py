from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ALLOWED_TABLES = frozenset({"customers", "products", "orders", "order_items"})

DENIED_ACTIONS = {
    sqlite3.SQLITE_CREATE_INDEX,
    sqlite3.SQLITE_CREATE_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_INDEX,
    sqlite3.SQLITE_CREATE_TEMP_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
    sqlite3.SQLITE_CREATE_TEMP_VIEW,
    sqlite3.SQLITE_CREATE_TRIGGER,
    sqlite3.SQLITE_CREATE_VIEW,
    sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_DROP_INDEX,
    sqlite3.SQLITE_DROP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_INDEX,
    sqlite3.SQLITE_DROP_TEMP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_TRIGGER,
    sqlite3.SQLITE_DROP_TEMP_VIEW,
    sqlite3.SQLITE_DROP_TRIGGER,
    sqlite3.SQLITE_DROP_VIEW,
    sqlite3.SQLITE_INSERT,
    sqlite3.SQLITE_PRAGMA,
    sqlite3.SQLITE_REINDEX,
    sqlite3.SQLITE_TRANSACTION,
    sqlite3.SQLITE_UPDATE,
    sqlite3.SQLITE_ATTACH,
    sqlite3.SQLITE_DETACH,
    sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_ANALYZE,
    sqlite3.SQLITE_CREATE_VTABLE,
    sqlite3.SQLITE_DROP_VTABLE,
    sqlite3.SQLITE_SAVEPOINT,
}


class QueryExecutionError(RuntimeError):
    """Raised when SQLite rejects or interrupts a query."""


@dataclass(frozen=True)
class QueryResult:
    dataframe: pd.DataFrame
    elapsed_ms: float
    returned_rows: int
    truncated: bool


def connect_read_only(database_path: Path) -> sqlite3.Connection:
    if not database_path.exists():
        raise FileNotFoundError(
            f"数据库不存在：{database_path}。请先运行 python scripts/generate_data.py"
        )
    uri = f"file:{database_path.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=1.0)
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 1000")

    def authorizer(action: int, arg1: str | None, arg2: str | None, *_: object) -> int:
        if action in DENIED_ACTIONS:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_READ and arg1 and arg1 not in ALLOWED_TABLES:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and (arg1 or arg2 or "").lower() == "load_extension":
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorizer)
    return connection


def execute_read_only(
    database_path: Path,
    sql: str,
    *,
    max_rows: int = 500,
    timeout_seconds: float = 3.0,
    max_steps: int = 200_000,
) -> QueryResult:
    """Execute validated SQL with defense-in-depth resource limits.

    The database is opened in URI read-only mode, an authorizer blocks mutating
    opcodes, a progress handler enforces time/VM-step limits, and an outer LIMIT
    caps materialized result rows.
    """

    start = time.monotonic()
    deadline = start + timeout_seconds
    steps = 0
    connection = connect_read_only(database_path)

    def progress() -> int:
        nonlocal steps
        steps += 1_000
        return int(steps > max_steps or time.monotonic() > deadline)

    connection.set_progress_handler(progress, 1_000)
    wrapped = f"SELECT * FROM ({sql.rstrip().rstrip(';')}) AS retailmind_result LIMIT ?"
    try:
        cursor = connection.execute(wrapped, (max_rows + 1,))
        columns = [item[0] for item in cursor.description or []]
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        message = str(exc)
        if "interrupted" in message.lower():
            message = "查询超过资源限制，已安全终止。请缩小时间范围或减少聚合维度。"
        raise QueryExecutionError(message) from exc
    finally:
        connection.close()

    truncated = len(rows) > max_rows
    visible_rows = rows[:max_rows]
    frame = pd.DataFrame(visible_rows, columns=columns)
    elapsed_ms = (time.monotonic() - start) * 1_000
    return QueryResult(frame, elapsed_ms, len(visible_rows), truncated)


def get_schema(database_path: Path) -> str:
    """Return a prompt-friendly schema without exposing SQLite internals."""

    if not database_path.exists():
        raise FileNotFoundError(f"数据库不存在：{database_path}")
    uri = f"file:{database_path.resolve().as_posix()}?mode=ro"
    # Schema introspection is internal application code. It uses a read-only URI;
    # the stricter runtime authorizer is reserved for model-generated queries.
    connection = sqlite3.connect(uri, uri=True, timeout=1.0)
    try:
        lines: list[str] = []
        for table in sorted(ALLOWED_TABLES):
            columns = connection.execute(f"PRAGMA table_info({table})").fetchall()
            rendered = ", ".join(f"{column[1]} {column[2]}" for column in columns)
            lines.append(f"{table}({rendered})")
        return "\n".join(lines)
    finally:
        connection.close()


def get_database_overview(database_path: Path) -> dict[str, object]:
    connection = connect_read_only(database_path)
    try:
        order_count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        product_count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        date_range = connection.execute(
            "SELECT MIN(order_date), MAX(order_date) FROM orders"
        ).fetchone()
        return {
            "orders": order_count,
            "products": product_count,
            "customers": customer_count,
            "min_date": date_range[0],
            "max_date": date_range[1],
        }
    finally:
        connection.close()
