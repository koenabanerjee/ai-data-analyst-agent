"""
app/agents/workflow.py — LangGraph agentic orchestration

State flows through:
  SchemaAgent → EDAAgent → MissingValueAgent → OutlierAgent
      → CorrelationAgent → InsightAgent → VisualizationAgent → ReportAgent

Each agent enriches the shared AgentState dict and can route conditionally.
"""
from __future__ import annotations

import json
import time
from typing import Any, TypedDict

import pandas as pd
from langgraph.graph import END, StateGraph

from app.utils.ai_client import get_ai_client
from app.utils.data_utils import (
    classify_columns,
    compute_column_stats,
    compute_correlation_matrix,
    detect_outliers_iqr,
    detect_outliers_zscore,
    detect_schema,
    recommend_imputation,
)
from app.utils.logging import get_logger
from app.utils.viz_utils import build_charts

logger = get_logger(__name__)


# ── Shared state ──────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    # inputs
    dataset_id: str
    df: Any  # pd.DataFrame
    file_type: str
    original_filename: str

    # schema agent
    schema: dict[str, Any]
    column_classes: dict[str, list[str]]

    # eda agent
    overview: dict[str, Any]
    column_stats: list[dict[str, Any]]

    # missing value agent
    missing_recommendations: list[dict[str, Any]]

    # outlier agent
    outlier_summary: dict[str, Any]

    # correlation agent
    correlation: dict[str, Any]

    # insight agent
    ai_insights: str

    # visualization agent
    charts: list[dict[str, Any]]

    # report agent
    report_sections: dict[str, Any]

    # control
    errors: list[str]
    agent_trace: list[str]


# ── Helper: safe append to trace ─────────────────────────────────────────────

def _trace(state: AgentState, msg: str) -> None:
    state.setdefault("agent_trace", []).append(msg)
    state.setdefault("errors", [])
    logger.info("[AgentTrace] %s", msg)


# ── Agent nodes ───────────────────────────────────────────────────────────────

async def schema_agent(state: AgentState) -> AgentState:
    _trace(state, "SchemaAgent: detecting schema and column types")
    df: pd.DataFrame = state["df"]
    try:
        schema = detect_schema(df)
        col_classes = classify_columns(df)
        state["schema"] = schema
        state["column_classes"] = col_classes
        _trace(state, f"SchemaAgent: found {len(schema)} columns — numeric={len(col_classes['numeric'])}, cat={len(col_classes['categorical'])}")
    except Exception as exc:
        state["errors"].append(f"SchemaAgent: {exc}")
        logger.exception("SchemaAgent failed")
    return state


async def eda_agent(state: AgentState) -> AgentState:
    _trace(state, "EDAAgent: computing dataset overview and per-column statistics")
    df: pd.DataFrame = state["df"]
    try:
        mem_kb = round(df.memory_usage(deep=True).sum() / 1024, 2)
        col_classes = state.get("column_classes", classify_columns(df))

        overview = {
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "total_nulls": int(df.isna().sum().sum()),
            "null_pct": round(float(df.isna().mean().mean() * 100), 2),
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage_kb": round(float(df.memory_usage(deep=True).sum() / 1024), 2),
            "numeric_columns": col_classes["numeric"],
            "categorical_columns": col_classes["categorical"],
            "datetime_columns": col_classes["datetime"],
        }

        col_stats = []
        for col in df.columns:
            try:
                col_stats.append(compute_column_stats(df[col], col))
            except Exception as e:
                logger.warning("EDAAgent: skipping column %s — %s", col, e)

        state["overview"] = overview
        state["column_stats"] = col_stats
        _trace(state, f"EDAAgent: overview complete. {overview['duplicate_rows']} duplicates, {overview['null_pct']}% nulls")
    except Exception as exc:
        state["errors"].append(f"EDAAgent: {exc}")
        logger.exception("EDAAgent failed")
    return state


async def missing_value_agent(state: AgentState) -> AgentState:
    _trace(state, "MissingValueAgent: recommending imputation strategies")
    df: pd.DataFrame = state["df"]
    schema = state.get("schema", {})
    try:
        recs = []
        for col in df.columns:
            if df[col].isna().any():
                recs.append(recommend_imputation(df[col], col, schema))
        state["missing_recommendations"] = recs
        _trace(state, f"MissingValueAgent: {len(recs)} columns with missing values analysed")
    except Exception as exc:
        state["errors"].append(f"MissingValueAgent: {exc}")
        logger.exception("MissingValueAgent failed")
    return state


async def outlier_agent(state: AgentState) -> AgentState:
    _trace(state, "OutlierAgent: IQR + Z-score outlier detection")
    df: pd.DataFrame = state["df"]
    col_classes = state.get("column_classes", classify_columns(df))
    numeric_cols = col_classes.get("numeric", [])
    try:
        summary: dict[str, Any] = {}
        total_outliers = 0
        for col in numeric_cols:
            iqr_res = detect_outliers_iqr(df[col])
            z_res = detect_outliers_zscore(df[col])
            summary[col] = {"iqr": iqr_res, "zscore": z_res}
            total_outliers += iqr_res.get("outlier_count", 0)

        state["outlier_summary"] = {
            "columns": summary,
            "total_outlier_cells": total_outliers,
            "numeric_columns_checked": len(numeric_cols),
        }
        _trace(state, f"OutlierAgent: {total_outliers} outliers found across {len(numeric_cols)} numeric columns")
    except Exception as exc:
        state["errors"].append(f"OutlierAgent: {exc}")
        logger.exception("OutlierAgent failed")
    return state


async def correlation_agent(state: AgentState) -> AgentState:
    _trace(state, "CorrelationAgent: computing Pearson correlation matrix")
    df: pd.DataFrame = state["df"]
    col_classes = state.get("column_classes", classify_columns(df))
    numeric_cols = col_classes.get("numeric", [])
    try:
        corr = compute_correlation_matrix(df, numeric_cols)
        state["correlation"] = corr
        sp = len(corr.get("strong_positive", []))
        sn = len(corr.get("strong_negative", []))
        _trace(state, f"CorrelationAgent: {sp} strong positive, {sn} strong negative correlations")
    except Exception as exc:
        state["errors"].append(f"CorrelationAgent: {exc}")
        logger.exception("CorrelationAgent failed")
    return state


async def insight_agent(state: AgentState) -> AgentState:
    _trace(state, "InsightAgent: generating AI-powered human-like insights")
    ai = get_ai_client()

    # Summarise state for the prompt (avoid sending full data)
    overview = state.get("overview", {})
    col_stats = state.get("column_stats", [])
    outlier_summary = state.get("outlier_summary", {})
    correlation = state.get("correlation", {})
    missing_recs = state.get("missing_recommendations", [])

    # Build a compact context for the AI
    numeric_summary = []
    for cs in col_stats:
        if cs.get("mean") is not None:
            numeric_summary.append(
                f"- {cs['name']}: mean={cs['mean']}, median={cs['median']}, std={cs['std']}, "
                f"skew={cs.get('skewness')}, nulls={cs['null_pct']}%"
            )

    strong_corr_text = ""
    sp = correlation.get("strong_positive", [])
    sn = correlation.get("strong_negative", [])
    if sp:
        strong_corr_text += "Strong positive correlations: " + ", ".join(f"{c['col1']}↔{c['col2']} (r={c['r']})" for c in sp[:5])
    if sn:
        strong_corr_text += "\nStrong negative correlations: " + ", ".join(f"{c['col1']}↔{c['col2']} (r={c['r']})" for c in sn[:5])

    system_prompt = """You are a senior data scientist writing an executive summary for a business analyst audience.
Your insights must be:
1. Human-like and narrative — avoid bullet-point statistics dumps
2. Interpretive — explain WHAT patterns mean, not just WHAT they are
3. Actionable — provide concrete recommendations
4. Professional — use data journalism tone
5. Structured — use markdown headers: ## Key Findings, ## Patterns & Trends, ## Anomalies, ## Recommendations

Never say "Average salary = 50000". Instead say "Compensation clusters around mid-range values, suggesting a relatively flat salary band — which may indicate limited senior roles or compressed pay scales."
"""

    user_prompt = f"""Dataset: {state.get('original_filename', 'Unknown')}
Rows: {overview.get('row_count', 0)} | Columns: {overview.get('column_count', 0)}
Duplicate rows: {overview.get('duplicate_rows', 0)} ({overview.get('null_pct', 0)}% nulls overall)
Numeric columns: {', '.join(overview.get('numeric_columns', []))}
Categorical columns: {', '.join(overview.get('categorical_columns', []))}

Numeric statistics:
{chr(10).join(numeric_summary[:15])}

Correlation insights:
{strong_corr_text or 'No strong correlations found.'}

Missing value issues:
{', '.join(f"{r['column']} ({r['null_pct']}%)" for r in missing_recs[:10]) or 'None'}

Total outliers detected (IQR): {outlier_summary.get('total_outlier_cells', 0)}

Write a professional data analysis report with genuine insights. Be specific about column names.
"""

    try:
        insights = await ai.complete(system_prompt, user_prompt, temperature=0.4, max_tokens=2000)
        state["ai_insights"] = insights
        _trace(state, "InsightAgent: AI insights generated successfully")
    except Exception as exc:
        state["ai_insights"] = "Insight generation failed — check AI API key configuration."
        state["errors"].append(f"InsightAgent: {exc}")
        logger.exception("InsightAgent failed")
    return state


async def visualization_agent(state: AgentState) -> AgentState:
    _trace(state, "VisualizationAgent: autonomously selecting and building charts")
    df: pd.DataFrame = state["df"]
    col_classes = state.get("column_classes", classify_columns(df))
    try:
        charts = build_charts(df, col_classes)
        state["charts"] = charts
        _trace(state, f"VisualizationAgent: {len(charts)} charts generated")
    except Exception as exc:
        state["charts"] = []
        state["errors"].append(f"VisualizationAgent: {exc}")
        logger.exception("VisualizationAgent failed")
    return state


async def report_agent(state: AgentState) -> AgentState:
    _trace(state, "ReportAgent: assembling report sections")
    try:
        state["report_sections"] = {
            "dataset_name": state.get("original_filename", "Dataset"),
            "overview": state.get("overview", {}),
            "column_stats": state.get("column_stats", []),
            "missing_recommendations": state.get("missing_recommendations", []),
            "outlier_summary": state.get("outlier_summary", {}),
            "correlation": state.get("correlation", {}),
            "ai_insights": state.get("ai_insights", ""),
            "charts": state.get("charts", []),
        }
        _trace(state, "ReportAgent: sections assembled")
    except Exception as exc:
        state["errors"].append(f"ReportAgent: {exc}")
        logger.exception("ReportAgent failed")
    return state


# ── Graph construction ────────────────────────────────────────────────────────

def build_eda_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("schema_agent", schema_agent)
    graph.add_node("eda_agent", eda_agent)
    graph.add_node("missing_value_agent", missing_value_agent)
    graph.add_node("outlier_agent", outlier_agent)
    graph.add_node("correlation_agent", correlation_agent)
    graph.add_node("insight_agent", insight_agent)
    graph.add_node("visualization_agent", visualization_agent)
    graph.add_node("report_agent", report_agent)

    graph.set_entry_point("schema_agent")
    graph.add_edge("schema_agent", "eda_agent")
    graph.add_edge("eda_agent", "missing_value_agent")
    graph.add_edge("missing_value_agent", "outlier_agent")
    graph.add_edge("outlier_agent", "correlation_agent")
    graph.add_edge("correlation_agent", "insight_agent")
    graph.add_edge("insight_agent", "visualization_agent")
    graph.add_edge("visualization_agent", "report_agent")
    graph.add_edge("report_agent", END)

    return graph


# ── Query agent (standalone, called on demand) ────────────────────────────────

async def query_agent(
    df: pd.DataFrame,
    question: str,
    eda_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Intelligent NL query agent. Given a question and pre-computed EDA context,
    returns an answer + optional chart spec.
    """
    ai = get_ai_client()
    col_classes = classify_columns(df)

    # Summarize dataset for the prompt
    overview = eda_result.get("overview", {})
    col_stats = eda_result.get("column_stats", [])

    stats_summary = []
    for cs in col_stats[:20]:
        if cs.get("mean") is not None:
            stats_summary.append(f"{cs['name']}: mean={cs['mean']}, std={cs['std']}, min={cs['min']}, max={cs['max']}, nulls={cs['null_pct']}%")
        else:
            stats_summary.append(f"{cs['name']}: {cs['unique_count']} unique values, nulls={cs['null_pct']}%")

    corr = eda_result.get("correlation", {})
    sp = corr.get("strong_positive", [])
    sn = corr.get("strong_negative", [])

    system_prompt = """You are an expert data analyst answering questions about a dataset.

Rules:
1. Answer in clear, professional prose — like a senior analyst explaining to a stakeholder
2. Reference specific column names, values, and statistics
3. If a chart would help, specify it in the JSON response
4. Always explain WHY, not just WHAT
5. Be concise but complete (150-300 words ideal)

Respond ONLY with this JSON structure:
{
  "answer": "<markdown-formatted answer>",
  "chart_spec": null OR {
    "chart_type": "histogram|scatter|bar|line|box|heatmap|pie",
    "title": "...",
    "x_column": "...",
    "y_column": "...",
    "reason": "..."
  }
}"""

    user_prompt = f"""Dataset: {overview.get('row_count', 0)} rows × {overview.get('column_count', 0)} columns
Numeric columns: {', '.join(col_classes.get('numeric', []))}
Categorical columns: {', '.join(col_classes.get('categorical', []))}

Column statistics:
{chr(10).join(stats_summary[:20])}

Strong correlations: {', '.join(f"{c['col1']}↔{c['col2']} (r={c['r']})" for c in (sp + sn)[:5]) or 'None'}
Outliers detected: {eda_result.get('outlier_summary', {}).get('total_outlier_cells', 0)}

User question: {question}"""

    try:
        result = await ai.complete_json(system_prompt, user_prompt, temperature=0.3)
    except Exception as exc:
        logger.exception("QueryAgent AI call failed")
        result = {
            "answer": f"I was unable to answer your question due to an AI error: {exc}",
            "chart_spec": None,
        }

    # If chart_spec requested, build the actual chart
    chart_json = None
    cs = result.get("chart_spec")
    if cs and isinstance(cs, dict):
        try:
            from app.utils.viz_utils import build_single_chart
            chart_json = build_single_chart(df, cs)
        except Exception as exc:
            logger.warning("QueryAgent chart build failed: %s", exc)

    return {
        "answer": result.get("answer", "No answer generated."),
        "chart": chart_json,
        "agent_trace": {"nodes": ["query_agent"], "question": question},
    }
