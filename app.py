from __future__ import annotations

import streamlit as st

from retailmind.charts import build_chart
from retailmind.config import settings
from retailmind.database import get_database_overview
from retailmind.demo import DEMO_QUERIES
from retailmind.service import run_analysis


st.set_page_config(
    page_title="RetailMind · AI 零售问数助手",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --mint:#18C6A3; --ink:#09111F; --panel:#111D30; --muted:#8FA2BD; }
    .stApp { background:
        radial-gradient(circle at 12% 4%, rgba(24,198,163,.12), transparent 25rem),
        radial-gradient(circle at 92% 12%, rgba(124,131,253,.10), transparent 26rem),
        #09111F; }
    [data-testid="stHeader"] { background: rgba(9,17,31,.68); backdrop-filter: blur(12px); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#0C1728 0%,#0A1322 100%); border-right:1px solid rgba(148,163,184,.12); }
    .block-container { max-width: 1220px; padding-top: 2.4rem; padding-bottom: 4rem; }
    .brand-row { display:flex; align-items:center; gap:16px; margin-bottom:8px; }
    .brand-mark { width:48px; height:48px; border-radius:14px; display:grid; place-items:center;
        font-size:25px; color:#07111C; background:linear-gradient(135deg,#46E3BE,#18C6A3 52%,#6EE7D1);
        box-shadow:0 12px 32px rgba(24,198,163,.22); }
    .brand-title { font-size:2.05rem; line-height:1; font-weight:760; letter-spacing:-.04em; color:#F4F8FD; }
    .brand-subtitle { color:#8FA2BD; font-size:.94rem; margin-top:7px; letter-spacing:.02em; }
    .eyebrow { color:#5FE1C1; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:700; margin-bottom:.8rem; }
    .hero { border:1px solid rgba(148,163,184,.14); border-radius:22px; padding:28px 30px 25px;
        background:linear-gradient(135deg,rgba(17,29,48,.96),rgba(13,24,41,.90));
        box-shadow:0 24px 80px rgba(0,0,0,.20); margin:1.45rem 0 1.3rem; }
    .hero h2 { color:#F5F8FC; font-size:1.72rem; letter-spacing:-.03em; margin:.1rem 0 .5rem; }
    .hero p { color:#9AAAC1; margin:0; max-width:780px; line-height:1.72; }
    .mode-badge { display:inline-flex; align-items:center; gap:7px; color:#A7F3D0; background:rgba(24,198,163,.10);
        border:1px solid rgba(24,198,163,.24); border-radius:999px; padding:7px 11px; font-size:.78rem; font-weight:650; }
    .mode-dot { width:7px; height:7px; border-radius:50%; background:#26D9B3; box-shadow:0 0 0 4px rgba(38,217,179,.10); }
    [data-testid="stMetric"] { background:rgba(17,29,48,.78); border:1px solid rgba(148,163,184,.13); border-radius:16px; padding:14px 16px; }
    [data-testid="stMetricLabel"] { color:#8FA2BD; }
    [data-testid="stMetricValue"] { color:#F3F7FC; letter-spacing:-.03em; }
    .insight-card { border-left:3px solid #18C6A3; background:rgba(17,29,48,.72); border-radius:4px 16px 16px 4px; padding:18px 20px; }
    .subtle { color:#71839D; font-size:.82rem; }
    div[data-testid="stDataFrame"] { border:1px solid rgba(148,163,184,.14); border-radius:14px; overflow:hidden; }
    .stButton > button, .stDownloadButton > button { border-radius:11px; border-color:rgba(148,163,184,.25); }
    .stButton > button[kind="primary"], .stFormSubmitButton > button { background:linear-gradient(135deg,#20D2AD,#13B894); color:#06130F; border:none; font-weight:750; }
    code { color:#A7F3D0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def database_overview() -> dict[str, object]:
    return get_database_overview(settings.database_path)


overview = database_overview()
has_api_key = bool(settings.openai_api_key)

with st.sidebar:
    st.markdown("### RetailMind")
    st.caption("LLM-powered retail intelligence")
    st.divider()
    available_modes = ["体验模式（无需 Key）"]
    if has_api_key:
        available_modes.insert(0, "AI 模式（实时生成）")
    selected_mode = st.radio("运行模式", available_modes, index=0)
    mode = "ai" if selected_mode.startswith("AI") else "demo"

    if mode == "demo":
        st.info("预设问句映射到已审查 SQL；仍会实时查询 SQLite，但不会调用 LLM。")
    else:
        st.success(f"已连接模型：{settings.openai_model}")

    st.markdown("#### 数据集")
    st.caption(f"{overview['min_date']} → {overview['max_date']}")
    col_a, col_b = st.columns(2)
    col_a.metric("订单", f"{int(overview['orders']):,}")
    col_b.metric("商品", f"{int(overview['products']):,}")
    st.metric("客户", f"{int(overview['customers']):,}")

    st.divider()
    st.caption("安全策略：SELECT-only · 表白名单 · 只读连接 · 行数/时间/VM 步数限制")

st.markdown(
    """
    <div class="brand-row">
      <div class="brand-mark">◈</div>
      <div><div class="brand-title">RetailMind</div><div class="brand-subtitle">零售业务智能问数助手</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

badge_text = "实时 LLM Text-to-SQL" if mode == "ai" else "无需 API Key 的真实查询演示"
st.markdown(
    f"""
    <section class="hero">
      <div class="eyebrow">Ask your business data</div>
      <span class="mode-badge"><span class="mode-dot"></span>{badge_text}</span>
      <h2>把业务问题，变成可验证的数据答案</h2>
      <p>用自然语言分析销售趋势、商品表现、渠道效率与客户结构。每条 SQL 都会先经过安全校验，再以只读方式执行。</p>
    </section>
    """,
    unsafe_allow_html=True,
)

examples = [item.question for item in DEMO_QUERIES]
with st.form("question_form"):
    if mode == "demo":
        question = st.selectbox("选择一个演示问题", examples, index=0)
        st.caption("体验模式不进行实时自然语言转 SQL；所选问题将执行仓库内已审查的 SQL。")
    else:
        example = st.selectbox("从示例开始（可选）", ["自定义问题"] + examples)
        custom = st.text_area(
            "输入业务问题",
            placeholder="例如：2025 年各季度销售额和毛利润有什么变化？",
            height=104,
        )
        question = custom.strip() or (example if example != "自定义问题" else "")
    submitted = st.form_submit_button("运行分析  →", type="primary", width="stretch")

if submitted:
    if not question:
        st.warning("请先输入一个业务问题。")
    else:
        try:
            with st.status("正在规划查询…", expanded=True) as status:
                st.write("解析问题并准备 SQL")
                result = run_analysis(question, mode, settings)
                st.write("安全校验通过，查询已完成")
                status.update(label="分析完成", state="complete", expanded=False)
            st.session_state["last_result"] = result
        except Exception as exc:
            st.session_state.pop("last_result", None)
            st.error(f"分析失败：{exc}")
            st.caption("请检查问题是否属于当前零售数据范围；AI 模式还需确认 API Key、模型名与网络连接。")

result = st.session_state.get("last_result")
if result is not None:
    st.markdown(f"## {result.title}")
    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric("返回记录", f"{result.query.returned_rows:,}")
    metric_b.metric("查询耗时", f"{result.query.elapsed_ms:.1f} ms")
    metric_c.metric("涉及表", str(len(result.audit.tables)))
    metric_d.metric("执行模式", "实时 AI" if mode == "ai" else "预设演示")

    if result.query.truncated:
        st.warning(f"结果超过安全上限，仅展示前 {settings.max_rows} 行。")

    chart_tab, data_tab, sql_tab = st.tabs(["趋势洞察", "数据明细", "SQL 与安全审计"])
    with chart_tab:
        chart = build_chart(result.dataframe, result.title, result.chart_hint)
        if chart is not None:
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
        else:
            st.info("当前结果更适合表格阅读，未自动生成图表。")
        st.markdown("#### 数据解读")
        st.markdown(result.explanation)
        st.caption(f"解释来源：{result.explanation_source}")

    with data_tab:
        st.dataframe(result.dataframe, width="stretch", hide_index=True)
        csv_bytes = result.dataframe.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "下载 CSV",
            data=csv_bytes,
            file_name="retailmind_result.csv",
            mime="text/csv",
        )

    with sql_tab:
        st.code(result.audit.sql, language="sql")
        st.caption("涉及数据表：" + "、".join(result.audit.tables))
        for check in result.audit.checks:
            st.markdown(f"✓ {check}")
        if mode == "demo":
            st.info("这条 SQL 来自仓库内的预设问题映射，不是 LLM 实时生成。")

st.divider()
st.caption("RetailMind MVP · 合成数据仅用于作品演示 · 查询结果请以 SQL 与数据明细为准")
