from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from retailmind.config import Settings
from retailmind.database import QueryResult, execute_read_only, get_database_overview, get_schema
from retailmind.demo import get_demo_query
from retailmind.llm import SQLPlan, build_grounded_summary, explain_with_llm, generate_sql
from retailmind.sql_guard import SQLAudit, validate_sql


@dataclass(frozen=True)
class AnalysisResult:
    question: str
    title: str
    chart_hint: str
    explanation: str
    explanation_source: str
    audit: SQLAudit
    query: QueryResult

    @property
    def dataframe(self) -> pd.DataFrame:
        return self.query.dataframe


def run_analysis(question: str, mode: str, settings: Settings) -> AnalysisResult:
    overview = get_database_overview(settings.database_path)
    if mode == "demo":
        demo = get_demo_query(question)
        plan = SQLPlan(demo.title, demo.sql, demo.chart_hint, demo.description)
    elif mode == "ai":
        if not settings.openai_api_key:
            raise ValueError("AI 模式需要在环境变量中设置 OPENAI_API_KEY。")
        plan = generate_sql(
            question,
            schema=get_schema(settings.database_path),
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            data_min_date=str(overview["min_date"]),
            data_max_date=str(overview["max_date"]),
        )
    else:
        raise ValueError(f"未知运行模式：{mode}")

    audit = validate_sql(plan.sql)
    query_result = execute_read_only(
        settings.database_path,
        audit.sql,
        max_rows=settings.max_rows,
        timeout_seconds=settings.query_timeout_seconds,
        max_steps=settings.max_sql_steps,
    )

    if mode == "ai" and settings.openai_api_key:
        explanation, used_llm = explain_with_llm(
            question,
            audit.sql,
            query_result.dataframe,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
        source = "LLM（数字已与结果集核验）" if used_llm else "本地确定性摘要"
    else:
        explanation = build_grounded_summary(query_result.dataframe)
        source = "本地确定性摘要（体验模式）"

    return AnalysisResult(
        question=question,
        title=plan.title,
        chart_hint=plan.chart_hint,
        explanation=explanation,
        explanation_source=source,
        audit=audit,
        query=query_result,
    )
