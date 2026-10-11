# RetailMind Demo 指南

## 90 秒展示脚本

1. 启动 `streamlit run app.py`，先指出左侧当前是“体验模式（无需 Key）”。
2. 说明体验模式不是实时 LLM：问题与 SQL 映射已审查，但每次都真实查询 SQLite。
3. 运行“每月销售额趋势如何？”，展示折线图、返回行数和查询耗时。
4. 打开“数据明细”，说明图表和摘要均来自这份实际结果，可下载 CSV。
5. 打开“SQL 与安全审计”，展示 SQL、涉及表和五项安全检查。
6. 切换到“各品类的销售额和利润对比”，展示系统自动改为品类柱状图。
7. 如果已配置 `OPENAI_API_KEY`，切换到 AI 模式并输入一个新问题；强调 SQL 仍会经过同一安全链路。

## 截取真实运行图

截图脚本不会伪造页面：它会访问正在运行的 Streamlit、点击“运行分析”、等待真实查询完成，再保存全页截图。

```bash
streamlit run app.py
```

另开终端：

```bash
pip install playwright
playwright install chromium
python scripts/capture_screenshot.py
```

默认输出：`docs/screenshots/retailmind-demo.png`。

可自定义地址和输出位置：

```bash
python scripts/capture_screenshot.py \
  --url http://localhost:8501 \
  --output docs/screenshots/retailmind-demo.png
```

## 公开演示前检查

- 确认 `.env` 没有被 Git 跟踪。
- 体验模式无需 secret，适合直接部署公开演示。
- 若启用 AI 模式，在部署平台的 Secret/Environment Variables 中配置 `OPENAI_API_KEY`。
- 运行 `pytest -q` 和 `python scripts/generate_data.py` 后再次冒烟测试。
- 公开说明数据为合成数据，不代表真实企业经营情况。

