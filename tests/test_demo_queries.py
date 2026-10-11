import pytest

from retailmind.config import settings
from retailmind.demo import DEMO_QUERIES
from retailmind.service import run_analysis


@pytest.mark.parametrize("question", [item.question for item in DEMO_QUERIES])
def test_every_demo_query_runs_against_real_database(question: str) -> None:
    result = run_analysis(question, "demo", settings)
    assert not result.dataframe.empty
    assert result.query.returned_rows <= settings.max_rows
    assert result.explanation_source.startswith("本地确定性摘要")
    assert result.audit.tables


def test_demo_mode_rejects_unlisted_question() -> None:
    with pytest.raises(ValueError, match="仅支持"):
        run_analysis("请随便猜一个数字", "demo", settings)

