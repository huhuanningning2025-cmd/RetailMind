import pandas as pd

from retailmind.llm import build_grounded_summary


def test_summary_uses_dataframe_values() -> None:
    frame = pd.DataFrame({"品类": ["家居", "数码"], "销售额": [100.0, 150.0]})
    summary = build_grounded_summary(frame)
    assert "数码" in summary
    assert "150.00" in summary
    assert "50.00%" in summary


def test_empty_summary_is_explicit() -> None:
    assert "没有返回记录" in build_grounded_summary(pd.DataFrame())
