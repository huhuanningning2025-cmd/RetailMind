import sqlite3

import pytest

from retailmind.config import settings
from retailmind.database import QueryExecutionError, execute_read_only, get_database_overview, get_schema


def test_database_is_healthy() -> None:
    overview = get_database_overview(settings.database_path)
    assert overview["orders"] == 1800
    assert overview["products"] == 28
    assert overview["customers"] == 240
    assert overview["min_date"] == "2024-01-01"
    assert overview["max_date"] == "2025-12-31"
    assert "order_items(" in get_schema(settings.database_path)


def test_query_result_is_limited() -> None:
    result = execute_read_only(settings.database_path, "SELECT * FROM orders", max_rows=10)
    assert result.returned_rows == 10
    assert result.truncated is True


def test_authorizer_blocks_mutation_even_without_guard() -> None:
    with pytest.raises(QueryExecutionError):
        execute_read_only(settings.database_path, "DELETE FROM orders")
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1800

