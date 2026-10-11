import pytest

from retailmind.sql_guard import UnsafeSQLError, validate_sql


def test_accepts_read_only_aggregate() -> None:
    audit = validate_sql(
        "SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY n DESC"
    )
    assert audit.tables == ("orders",)
    assert "SELECT" in audit.sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM orders",
        "SELECT * FROM orders; DROP TABLE orders",
        "PRAGMA table_info(orders)",
        "SELECT * FROM sqlite_master",
        "WITH RECURSIVE seq(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM seq) SELECT * FROM seq",
        "SELECT * FROM orders -- hide a second statement",
    ],
)
def test_rejects_unsafe_sql(sql: str) -> None:
    with pytest.raises(UnsafeSQLError):
        validate_sql(sql)


def test_accepts_non_recursive_cte() -> None:
    audit = validate_sql(
        "WITH complete AS (SELECT * FROM orders WHERE status='已完成') SELECT COUNT(*) FROM complete"
    )
    assert audit.ctes == 1
    assert audit.tables == ("orders",)

