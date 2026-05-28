"""
app/utils/data_utils.py — pandas/numpy helpers shared across agents
"""
from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any

import chardet
import numpy as np
import pandas as pd
from scipy import stats

from app.utils.logging import get_logger

logger = get_logger(__name__)


# ── Loading ───────────────────────────────────────────────────────────────────

def load_dataframe(file_path: str | Path, file_type: str) -> pd.DataFrame:
    """Load CSV or XLSX into a DataFrame with robust encoding detection."""
    path = Path(file_path)
    if file_type == "csv":
        raw = path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or "utf-8"
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=encoding, low_memory=False)
        except Exception:
            df = pd.read_csv(io.BytesIO(raw), encoding="latin-1", low_memory=False)
    elif file_type in ("xlsx", "xls"):
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    # strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]
    return df


# ── Schema detection ─────────────────────────────────────────────────────────

def detect_schema(df: pd.DataFrame) -> dict[str, Any]:
    """Return schema metadata for a dataframe."""
    schema: dict[str, Any] = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        inferred = _infer_semantic_type(df[col])
        schema[col] = {
            "dtype": dtype,
            "semantic_type": inferred,
            "nullable": bool(df[col].isna().any()),
        }
    return schema


def _infer_semantic_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        if series.nunique() <= 20 and series.nunique() / max(len(series), 1) < 0.05:
            return "categorical_numeric"
        return "numeric"
    # try parsing as datetime
    try:
        converted = pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
        if converted.notna().sum() / max(len(series), 1) > 0.8:
            return "datetime"
    except Exception:
        pass
    if series.nunique() <= 50:
        return "categorical"
    return "text"


# ── Column classification ─────────────────────────────────────────────────────

def classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    schema = detect_schema(df)
    numeric, categorical, datetime_cols = [], [], []
    for col, info in schema.items():
        st = info["semantic_type"]
        if st in ("numeric", "categorical_numeric"):
            numeric.append(col)
        elif st == "datetime":
            datetime_cols.append(col)
        else:
            categorical.append(col)
    return {"numeric": numeric, "categorical": categorical, "datetime": datetime_cols}


# ── Statistics ────────────────────────────────────────────────────────────────

def compute_column_stats(series: pd.Series, col_name: str) -> dict[str, Any]:
    """Full descriptive stats for one column."""
    base: dict[str, Any] = {
        "name": col_name,
        "dtype": str(series.dtype),
        "null_count": int(series.isna().sum()),
        "null_pct": round(series.isna().mean() * 100, 2),
        "unique_count": int(series.nunique()),
        "sample_values": _safe_sample(series),
    }

    if pd.api.types.is_numeric_dtype(series):
        clean = series.dropna()
        if len(clean) == 0:
            return base
        try:
            mode_val = series.mode().iloc[0] if not series.mode().empty else None
        except Exception:
            mode_val = None

        base.update(
            {
                "mean": _safe_float(clean.mean()),
                "median": _safe_float(clean.median()),
                "mode": _safe_scalar(mode_val),
                "std": _safe_float(clean.std()),
                "variance": _safe_float(clean.var()),
                "min": _safe_float(clean.min()),
                "max": _safe_float(clean.max()),
                "q1": _safe_float(clean.quantile(0.25)),
                "q3": _safe_float(clean.quantile(0.75)),
                "skewness": _safe_float(stats.skew(clean)),
                "kurtosis": _safe_float(stats.kurtosis(clean)),
            }
        )
    return base


def _safe_float(val: Any) -> float | None:
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else round(f, 4)
    except Exception:
        return None


def _safe_scalar(val: Any) -> Any:
    if val is None:
        return None
    try:
        if isinstance(val, (np.integer,)):
            return int(val)
        if isinstance(val, (np.floating,)):
            return _safe_float(val)
        return val
    except Exception:
        return str(val)


def _safe_sample(series: pd.Series, n: int = 5) -> list[Any]:
    try:
        vals = series.dropna().unique()[:n]
        return [_safe_scalar(v) for v in vals]
    except Exception:
        return []


# ── Outlier detection ────────────────────────────────────────────────────────

def detect_outliers_iqr(series: pd.Series) -> dict[str, Any]:
    clean = series.dropna()
    if len(clean) < 4:
        return {"method": "iqr", "outlier_count": 0, "outlier_pct": 0, "bounds": {}}
    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (clean < lower) | (clean > upper)
    outliers = clean[mask]
    return {
        "method": "iqr",
        "outlier_count": int(mask.sum()),
        "outlier_pct": round(mask.mean() * 100, 2),
        "bounds": {"lower": _safe_float(lower), "upper": _safe_float(upper)},
        "outlier_values": [_safe_float(v) for v in outliers.head(10).tolist()],
    }


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> dict[str, Any]:
    clean = series.dropna()
    if len(clean) < 4:
        return {"method": "zscore", "outlier_count": 0, "outlier_pct": 0}
    z = np.abs(stats.zscore(clean))
    mask = z > threshold
    return {
        "method": "zscore",
        "threshold": threshold,
        "outlier_count": int(mask.sum()),
        "outlier_pct": round(mask.mean() * 100, 2),
    }


# ── Missing value recommendations ────────────────────────────────────────────

def recommend_imputation(series: pd.Series, col_name: str, schema: dict) -> dict[str, Any]:
    null_pct = series.isna().mean() * 100
    semantic = schema.get(col_name, {}).get("semantic_type", "")

    if null_pct == 0:
        return {"column": col_name, "null_pct": 0, "recommendation": "none", "reason": "No missing values."}

    if null_pct > 60:
        return {
            "column": col_name,
            "null_pct": round(null_pct, 2),
            "recommendation": "drop_column",
            "reason": f"{null_pct:.1f}% of values are missing. Imputation would introduce excessive noise; dropping the column is safer.",
        }

    if semantic in ("numeric",):
        sk = _safe_float(series.skew()) or 0
        if abs(sk) > 1:
            return {
                "column": col_name,
                "null_pct": round(null_pct, 2),
                "recommendation": "median_imputation",
                "reason": f"Column is numeric and right-skewed (skewness={sk:.2f}). Median is more robust than mean for skewed distributions.",
            }
        return {
            "column": col_name,
            "null_pct": round(null_pct, 2),
            "recommendation": "mean_imputation",
            "reason": f"Column is numeric and approximately symmetric. Mean imputation preserves distribution characteristics.",
        }

    return {
        "column": col_name,
        "null_pct": round(null_pct, 2),
        "recommendation": "mode_imputation",
        "reason": "Column is categorical. Mode imputation replaces missing values with the most frequent category.",
    }


# ── Correlation ───────────────────────────────────────────────────────────────

def compute_correlation_matrix(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any]:
    if len(numeric_cols) < 2:
        return {}
    corr = df[numeric_cols].corr(method="pearson").round(4)

    strong_pos, strong_neg = [], []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr.iloc[i, j]
            if pd.isna(val):
                continue
            if val >= 0.7:
                strong_pos.append({"col1": cols[i], "col2": cols[j], "r": round(float(val), 4)})
            elif val <= -0.7:
                strong_neg.append({"col1": cols[i], "col2": cols[j], "r": round(float(val), 4)})

    return {
        "matrix": corr.to_dict(),
        "columns": cols,
        "strong_positive": strong_pos,
        "strong_negative": strong_neg,
    }
