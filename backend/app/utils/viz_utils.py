"""
app/utils/viz_utils.py — Plotly chart builders

The VisualizationAgent calls build_charts() which autonomously selects
chart types based on column semantics and dataset characteristics.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Plotly color theme — consistent across all charts
TEMPLATE = "plotly_dark"
PALETTE = px.colors.qualitative.Set2


def _fig_to_json(fig: go.Figure) -> dict[str, Any]:
    """Serialise figure to JSON-safe dict."""
    return json.loads(fig.to_json())


def build_charts(df: pd.DataFrame, col_classes: dict[str, list[str]]) -> list[dict[str, Any]]:
    """
    Autonomously build a curated set of charts.
    Returns list of chart specs each with plotly_json included.
    """
    charts = []
    numeric = col_classes.get("numeric", [])
    categorical = col_classes.get("categorical", [])
    datetime_cols = col_classes.get("datetime", [])

    # 1. Histograms for each numeric column (up to 6)
    for col in numeric[:6]:
        try:
            charts.append(_histogram(df, col))
        except Exception as e:
            logger.warning("Histogram failed for %s: %s", col, e)

    # 2. Box plots — all numeric in one figure
    if numeric:
        try:
            charts.append(_boxplot_multi(df, numeric[:8]))
        except Exception as e:
            logger.warning("Boxplot failed: %s", e)

    # 3. Correlation heatmap
    if len(numeric) >= 2:
        try:
            charts.append(_correlation_heatmap(df, numeric[:12]))
        except Exception as e:
            logger.warning("Heatmap failed: %s", e)

    # 4. Scatter plot — top 2 correlated numeric columns
    if len(numeric) >= 2:
        try:
            sub_corr = df[numeric[:8]].corr().abs()
            mat = sub_corr.to_numpy().copy()
            np.fill_diagonal(mat, 0)
            flat_idx = mat.argmax()
            i_idx, j_idx = divmod(flat_idx, mat.shape[1])
            col_a, col_b = numeric[:8][i_idx], numeric[:8][j_idx]
            charts.append(_scatter(df, col_a, col_b, categorical[0] if categorical else None))
        except Exception as e:
            logger.warning("Scatter failed: %s", e)

    # 5. Bar chart — top categorical column value counts
    for col in categorical[:2]:
        if df[col].nunique() <= 30:
            try:
                charts.append(_bar_counts(df, col))
            except Exception as e:
                logger.warning("Bar chart failed for %s: %s", col, e)

    # 6. Violin plot for numeric (first 3 vs first categorical)
    if numeric and categorical:
        try:
            charts.append(_violin(df, numeric[0], categorical[0]))
        except Exception as e:
            logger.warning("Violin failed: %s", e)

    # 7. Pie chart for first low-cardinality categorical
    for col in categorical:
        if 2 <= df[col].nunique() <= 8:
            try:
                charts.append(_pie(df, col))
            except Exception as e:
                logger.warning("Pie failed for %s: %s", col, e)
            break  # only one pie chart

    # 8. Line chart for datetime
    if datetime_cols and numeric:
        try:
            charts.append(_line(df, datetime_cols[0], numeric[0]))
        except Exception as e:
            logger.warning("Line chart failed: %s", e)

    return charts


# ── Individual chart builders ─────────────────────────────────────────────────

def _histogram(df: pd.DataFrame, col: str) -> dict[str, Any]:
    fig = px.histogram(
        df, x=col, nbins=40, template=TEMPLATE, title=f"Distribution of {col}",
        color_discrete_sequence=[PALETTE[0]],
        labels={col: col},
        marginal="box",
    )
    fig.update_layout(bargap=0.05, height=400)
    return {
        "chart_type": "histogram",
        "title": f"Distribution of {col}",
        "column": col,
        "reason": f"Histogram reveals the frequency distribution and skewness of '{col}', helping identify whether values are normally distributed or concentrated in specific ranges.",
        "plotly_json": _fig_to_json(fig),
    }


def _boxplot_multi(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any]:
    # Normalize each column to compare on same scale
    normed = df[numeric_cols].apply(lambda s: (s - s.mean()) / s.std() if s.std() != 0 else s)
    fig = go.Figure()
    for i, col in enumerate(numeric_cols):
        fig.add_trace(go.Box(y=normed[col].dropna(), name=col, marker_color=PALETTE[i % len(PALETTE)]))
    fig.update_layout(
        title="Box Plots — Normalized Numeric Columns",
        template=TEMPLATE,
        height=450,
        showlegend=False,
    )
    return {
        "chart_type": "boxplot",
        "title": "Box Plots — Normalized Numeric Columns",
        "column": None,
        "reason": "Box plots expose median, spread, and outliers for all numeric columns simultaneously. Normalization allows fair visual comparison across different scales.",
        "plotly_json": _fig_to_json(fig),
    }


def _correlation_heatmap(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any]:
    corr = df[numeric_cols].corr().round(2)
    fig = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        template=TEMPLATE,
        title="Pearson Correlation Heatmap",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
    )
    fig.update_layout(height=500)
    return {
        "chart_type": "heatmap",
        "title": "Pearson Correlation Heatmap",
        "column": None,
        "reason": "The heatmap reveals linear relationships between numeric variables. Red indicates strong positive correlation, blue indicates strong negative correlation.",
        "plotly_json": _fig_to_json(fig),
    }


def _scatter(df: pd.DataFrame, x: str, y: str, color_col: str | None = None) -> dict[str, Any]:
    sample = df.sample(min(2000, len(df)), random_state=42)
    kwargs: dict[str, Any] = dict(
        data_frame=sample, x=x, y=y,
        template=TEMPLATE, title=f"{x} vs {y}",
        opacity=0.6,
    )
    if color_col and sample[color_col].nunique() <= 15:
        kwargs["color"] = color_col
    fig = px.scatter(**kwargs)
    fig.update_layout(height=450)
    return {
        "chart_type": "scatter",
        "title": f"{x} vs {y}",
        "x_column": x,
        "y_column": y,
        "reason": f"Scatter plot between the two most-correlated numeric columns ('{x}' and '{y}') reveals the nature and strength of their relationship, including non-linear patterns.",
        "plotly_json": _fig_to_json(fig),
    }


def _bar_counts(df: pd.DataFrame, col: str) -> dict[str, Any]:
    counts = df[col].value_counts().reset_index().head(20)
    counts.columns = [col, "count"]
    fig = px.bar(
        counts, x=col, y="count",
        template=TEMPLATE,
        title=f"Value Counts — {col}",
        color_discrete_sequence=[PALETTE[2]],
        text_auto=True,
    )
    fig.update_layout(xaxis_tickangle=-35, height=420)
    return {
        "chart_type": "bar",
        "title": f"Value Counts — {col}",
        "column": col,
        "reason": f"Bar chart shows the frequency of each category in '{col}', highlighting dominant categories and rare values that may need attention.",
        "plotly_json": _fig_to_json(fig),
    }


def _violin(df: pd.DataFrame, y_col: str, x_col: str) -> dict[str, Any]:
    top_cats = df[x_col].value_counts().head(10).index.tolist()
    sub = df[df[x_col].isin(top_cats)]
    fig = px.violin(
        sub, y=y_col, x=x_col, box=True, points="outliers",
        template=TEMPLATE,
        title=f"Distribution of {y_col} by {x_col}",
        color=x_col,
    )
    fig.update_layout(height=450, showlegend=False)
    return {
        "chart_type": "violin",
        "title": f"Distribution of {y_col} by {x_col}",
        "x_column": x_col,
        "y_column": y_col,
        "reason": f"Violin plot shows the full distribution shape of '{y_col}' across each category of '{x_col}', revealing whether groups differ in spread, skewness, or central tendency.",
        "plotly_json": _fig_to_json(fig),
    }


def _pie(df: pd.DataFrame, col: str) -> dict[str, Any]:
    counts = df[col].value_counts().reset_index()
    counts.columns = [col, "count"]
    fig = px.pie(
        counts, names=col, values="count",
        template=TEMPLATE,
        title=f"Proportions — {col}",
        hole=0.3,
    )
    fig.update_layout(height=420)
    return {
        "chart_type": "pie",
        "title": f"Proportions — {col}",
        "column": col,
        "reason": f"Pie chart shows relative proportions of each category in '{col}', making it easy to identify dominant and minority groups.",
        "plotly_json": _fig_to_json(fig),
    }


def _line(df: pd.DataFrame, x_col: str, y_col: str) -> dict[str, Any]:
    sub = df[[x_col, y_col]].dropna().sort_values(x_col)
    fig = px.line(
        sub, x=x_col, y=y_col,
        template=TEMPLATE,
        title=f"{y_col} Over Time",
    )
    fig.update_layout(height=420)
    return {
        "chart_type": "line",
        "title": f"{y_col} Over Time",
        "x_column": x_col,
        "y_column": y_col,
        "reason": f"Line chart reveals temporal trends in '{y_col}' over '{x_col}', exposing seasonality, growth patterns, or sudden changes.",
        "plotly_json": _fig_to_json(fig),
    }


# ── On-demand chart builder for QueryAgent ───────────────────────────────────

def build_single_chart(df: pd.DataFrame, spec: dict[str, Any]) -> dict[str, Any] | None:
    """Build a single chart based on a QueryAgent chart_spec."""
    chart_type = spec.get("chart_type", "bar")
    x = spec.get("x_column")
    y = spec.get("y_column")

    try:
        if chart_type == "histogram" and x:
            return _histogram(df, x)
        if chart_type == "scatter" and x and y:
            return _scatter(df, x, y)
        if chart_type == "bar" and x:
            if y and pd.api.types.is_numeric_dtype(df[y]):
                grp = df.groupby(x)[y].mean().reset_index().sort_values(y, ascending=False).head(20)
                fig = px.bar(grp, x=x, y=y, template=TEMPLATE, title=spec.get("title", f"{y} by {x}"), text_auto=".2f")
                return {"chart_type": "bar", "title": spec.get("title"), "plotly_json": _fig_to_json(fig), "reason": spec.get("reason", "")}
            return _bar_counts(df, x)
        if chart_type == "box" and y:
            fig = px.box(df, y=y, template=TEMPLATE, title=spec.get("title", f"Box — {y}"))
            return {"chart_type": "box", "title": spec.get("title"), "plotly_json": _fig_to_json(fig), "reason": spec.get("reason", "")}
        if chart_type == "heatmap":
            numeric = df.select_dtypes(include="number").columns.tolist()
            return _correlation_heatmap(df, numeric[:12])
        if chart_type == "pie" and x:
            return _pie(df, x)
        if chart_type == "line" and x and y:
            return _line(df, x, y)
        if chart_type == "violin" and x and y:
            return _violin(df, y, x)
    except Exception as exc:
        logger.warning("build_single_chart failed for %s: %s", chart_type, exc)
    return None
