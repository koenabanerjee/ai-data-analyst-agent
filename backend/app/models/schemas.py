"""
app/models/schemas.py — Pydantic v2 request/response schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Dataset ───────────────────────────────────────────────────────────────────

class DatasetUploadResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    row_count: int
    column_count: int
    schema_info: dict[str, Any]
    status: str
    created_at: datetime


class DatasetListItem(BaseModel):
    id: str
    original_filename: str
    file_size: int
    file_type: str
    row_count: int
    column_count: int
    status: str
    created_at: datetime


class DatasetPreview(BaseModel):
    id: str
    columns: list[str]
    dtypes: dict[str, str]
    preview_rows: list[dict[str, Any]]
    row_count: int
    column_count: int


# ── EDA ───────────────────────────────────────────────────────────────────────

class ColumnStat(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: list[Any]
    # numeric only
    mean: float | None = None
    median: float | None = None
    mode: Any | None = None
    std: float | None = None
    variance: float | None = None
    min: float | None = None
    max: float | None = None
    q1: float | None = None
    q3: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None


class DatasetOverview(BaseModel):
    row_count: int
    column_count: int
    total_nulls: int
    null_pct: float
    duplicate_rows: int
    memory_usage_kb: float
    numeric_columns: list[str]
    categorical_columns: list[str]
    datetime_columns: list[str]


class EDAResult(BaseModel):
    dataset_id: str
    overview: DatasetOverview
    column_stats: list[ColumnStat]
    missing_value_recommendations: list[dict[str, Any]]
    outlier_summary: dict[str, Any]
    correlation_matrix: dict[str, Any] | None = None
    ai_insights: str
    status: str = "completed"


# ── Visualisation ─────────────────────────────────────────────────────────────

class ChartSpec(BaseModel):
    chart_type: str
    title: str
    column: str | None = None
    x_column: str | None = None
    y_column: str | None = None
    reason: str
    plotly_json: dict[str, Any]


class VisualisationResult(BaseModel):
    dataset_id: str
    charts: list[ChartSpec]
    status: str = "completed"


# ── Query ─────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class QueryResponse(BaseModel):
    id: str
    dataset_id: str
    question: str
    answer: str
    chart: dict[str, Any] | None = None
    agent_trace: dict[str, Any]
    created_at: datetime


# ── Report ────────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    id: str
    dataset_id: str
    file_path: str
    file_size: int
    created_at: datetime


# ── Generic ───────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class StatusResponse(BaseModel):
    status: str
    message: str
