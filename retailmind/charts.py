from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLORS = ["#18C6A3", "#7C83FD", "#F5B94C", "#FF7A8A", "#4AA8FF", "#A4D65E"]


def _style_figure(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title={"text": title, "x": 0.01, "xanchor": "left"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, PingFang SC, Microsoft YaHei, sans-serif", "color": "#D9E2F2"},
        colorway=COLORS,
        margin={"l": 30, "r": 24, "t": 64, "b": 30},
        hoverlabel={"bgcolor": "#17243A", "font_color": "#FFFFFF"},
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    figure.update_xaxes(showgrid=False, linecolor="rgba(148,163,184,.25)")
    figure.update_yaxes(gridcolor="rgba(148,163,184,.14)", zeroline=False)
    return figure


def build_chart(frame: pd.DataFrame, title: str, chart_hint: str = "table") -> go.Figure | None:
    if frame.empty:
        return None

    working = frame.copy()
    numeric = list(working.select_dtypes(include="number").columns)
    dimensions = [column for column in working.columns if column not in numeric]
    if not numeric:
        return None

    x_column = dimensions[0] if dimensions else working.columns[0]
    y_columns = [column for column in numeric if column != x_column][:2]
    if not y_columns:
        return None

    x_name = str(x_column).lower()
    looks_temporal = any(token in x_name for token in ("date", "day", "month", "year", "日期", "月份", "时间", "年度"))

    if chart_hint == "line" or looks_temporal:
        figure = px.line(
            working,
            x=x_column,
            y=y_columns,
            markers=True,
            color_discrete_sequence=COLORS,
        )
        figure.update_traces(line={"width": 3}, marker={"size": 7})
    else:
        display = working.head(20)
        figure = px.bar(
            display,
            x=x_column,
            y=y_columns,
            barmode="group",
            color_discrete_sequence=COLORS,
        )
        figure.update_traces(marker_line_width=0)
    return _style_figure(figure, title)

