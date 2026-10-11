from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_demo_ui_loads_and_runs_default_analysis() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()
    assert not app.exception
    assert app.selectbox[0].value == "每月销售额趋势如何？"
    assert {metric.label for metric in app.metric} >= {"订单", "商品", "客户"}

    app.button[0].click().run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["趋势洞察", "数据明细", "SQL 与安全审计"]
    assert len(app.dataframe) == 1
    assert len(app.code) == 1
    assert {metric.label for metric in app.metric} >= {"返回记录", "查询耗时", "涉及表", "执行模式"}
