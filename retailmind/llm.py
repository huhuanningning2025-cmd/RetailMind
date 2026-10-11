from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field


class LLMUnavailableError(RuntimeError):
    """Raised when the configured model cannot be used."""


class SQLPlanModel(BaseModel):
    title: str = Field(description="简短的中文分析标题")
    sql: str = Field(description="一条 SQLite SELECT 查询")
    chart_hint: Literal["line", "bar", "table"] = "table"
    interpretation_goal: str = Field(description="这条查询要回答的业务问题")


@dataclass(frozen=True)
class SQLPlan:
    title: str
    sql: str
    chart_hint: str
    interpretation_goal: str


def _client(api_key: str):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailableError("未安装 openai，请先执行 pip install -r requirements.txt") from exc
    return OpenAI(api_key=api_key, timeout=30.0, max_retries=1)


def generate_sql(
    question: str,
    *,
    schema: str,
    api_key: str,
    model: str,
    data_min_date: str,
    data_max_date: str,
) -> SQLPlan:
    system_prompt = f"""
你是 RetailMind 的 SQLite 查询规划器。只生成用于零售业务分析的单条只读查询。

数据库 Schema：
{schema}

数据日期范围：{data_min_date} 至 {data_max_date}。

强制规则：
1. 只允许 SELECT，或 WITH ... SELECT；禁止 PRAGMA、DDL、DML、多语句和递归 CTE。
2. 只能使用 Schema 中真实存在的表与字段，不得猜测。
3. 销售额 = order_items.quantity * order_items.unit_price * (1 - discount_rate)。
4. 毛利润 = quantity * (unit_price * (1 - discount_rate) - products.cost_price)。
5. 销售分析默认只统计 orders.status = '已完成'，除非用户明确询问取消/退款。
6. 比例与金额保留 2 位小数；明细查询加 LIMIT 100，聚合查询按业务含义排序。
7. 中文别名要清晰。不要在 SQL 中写注释。
8. 若用户说“最近/过去”，以数据最大日期 {data_max_date} 为锚点，不使用系统当前日期。
""".strip()
    try:
        completion = _client(api_key).chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            response_format=SQLPlanModel,
        )
        message = completion.choices[0].message
        if getattr(message, "refusal", None):
            raise LLMUnavailableError(f"模型拒绝了该请求：{message.refusal}")
        parsed = message.parsed
        if parsed is None:
            raise LLMUnavailableError("模型未返回可解析的 SQL 计划。")
    except LLMUnavailableError:
        raise
    except Exception as exc:
        raise LLMUnavailableError(f"LLM 调用失败：{exc}") from exc
    return SQLPlan(
        title=parsed.title,
        sql=parsed.sql,
        chart_hint=parsed.chart_hint,
        interpretation_goal=parsed.interpretation_goal,
    )


def _format_value(value: object) -> str:
    if pd.isna(value):
        return "空值"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def build_grounded_summary(frame: pd.DataFrame) -> str:
    """Create a deterministic explanation using only executed query results."""

    if frame.empty:
        return "本次查询没有返回记录。可以调整时间范围、筛选条件或问题表述后重试。"

    rows, cols = frame.shape
    numeric_columns = list(frame.select_dtypes(include="number").columns)
    dimension_columns = [column for column in frame.columns if column not in numeric_columns]
    lines = [f"查询实际返回 **{rows}** 行、**{cols}** 列。"]

    if numeric_columns:
        metric = numeric_columns[0]
        valid = frame.dropna(subset=[metric])
        if not valid.empty:
            top_index = valid[metric].idxmax()
            top_value = valid.loc[top_index, metric]
            if dimension_columns:
                label = valid.loc[top_index, dimension_columns[0]]
                lines.append(
                    f"按 **{metric}** 观察，最高项是 **{_format_value(label)}**，"
                    f"对应值为 **{_format_value(top_value)}**。"
                )
            else:
                lines.append(f"**{metric}** 的最大值为 **{_format_value(top_value)}**。")

        if rows > 1 and len(numeric_columns) >= 1:
            first = frame.iloc[0][metric]
            last = frame.iloc[-1][metric]
            if pd.notna(first) and pd.notna(last) and first != 0:
                change = (float(last) - float(first)) / abs(float(first)) * 100
                direction = "上升" if change > 0 else "下降" if change < 0 else "持平"
                lines.append(
                    f"首尾两项相比，**{metric}** {direction} **{abs(change):.2f}%**"
                    "（仅描述当前结果排序下的首尾变化）。"
                )

    lines.append("以上结论仅来自当前 SQL 返回的数据，不包含外部信息或未查询字段。")
    return "\n\n".join(lines)


def _number_tokens(text: str) -> set[str]:
    normalized: set[str] = set()
    for token in re.findall(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?", text):
        token = token.replace(",", "").lstrip("+")
        if "." in token:
            token = token.rstrip("0").rstrip(".")
        normalized.add(token or "0")
    return normalized


def _allowed_number_tokens(frame: pd.DataFrame) -> set[str]:
    payload = frame.to_json(orient="records", force_ascii=False, date_format="iso")
    allowed = _number_tokens(payload)
    allowed.update(str(value) for value in (len(frame), len(frame.columns)))
    return allowed


def explain_with_llm(
    question: str,
    sql: str,
    frame: pd.DataFrame,
    *,
    api_key: str,
    model: str,
) -> tuple[str, bool]:
    """Explain results and reject responses containing ungrounded numbers.

    Returns (explanation, used_llm). A deterministic explanation is used when
    the model fails or introduces a number absent from the result set.
    """

    fallback = build_grounded_summary(frame)
    if frame.empty:
        return fallback, False

    sample = frame.head(80).where(pd.notna(frame.head(80)), None).to_dict(orient="records")
    prompt = f"""
你是零售数据分析师。请只根据下面“SQL 实际结果”解释用户问题，不得补充常识数据、预测、原因归因或不存在的数字。
用 2-4 个简短中文要点回答。任何数字必须逐字来自结果；如需计算但结果未直接给出，就不要写。
若结果不足以支持结论，明确说“当前查询结果不足以判断”。

用户问题：{question}
执行 SQL：{sql}
SQL 实际结果（JSON）：{json.dumps(sample, ensure_ascii=False, default=str)}
""".strip()
    try:
        response = _client(api_key).responses.create(model=model, input=prompt)
        explanation = response.output_text.strip()
        if not explanation:
            return fallback, False
        if not _number_tokens(explanation).issubset(_allowed_number_tokens(frame)):
            return fallback + "\n\n> LLM 解释因包含结果集之外的数字，已被数据校验器拦截。", False
        return explanation, True
    except Exception:
        return fallback + "\n\n> LLM 解释暂不可用，已切换为本地确定性摘要。", False
