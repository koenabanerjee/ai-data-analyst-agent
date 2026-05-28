"""
app/services/dataset_service.py — business logic for dataset operations
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import Analysis, Dataset
from app.utils.data_utils import detect_schema, load_dataframe
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def save_uploaded_file(
    file_bytes: bytes, original_filename: str, file_type: str, db: AsyncSession
) -> Dataset:
    """Persist uploaded file and create Dataset record."""
    file_id = str(uuid.uuid4())
    ext = "csv" if file_type == "csv" else "xlsx"
    filename = f"{file_id}.{ext}"
    file_path = settings.upload_path / filename
    file_path.write_bytes(file_bytes)

    # Quick load to get row/column counts and schema
    df = load_dataframe(file_path, file_type)
    schema = detect_schema(df)

    dataset = Dataset(
        id=file_id,
        filename=filename,
        original_filename=original_filename,
        file_path=str(file_path),
        file_size=len(file_bytes),
        file_type=file_type,
        row_count=len(df),
        column_count=len(df.columns),
        schema_info=schema,
        status="ready",
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    logger.info("Dataset saved: %s (%d rows, %d cols)", original_filename, len(df), len(df.columns))
    return dataset


async def get_dataset(dataset_id: str, db: AsyncSession) -> Dataset | None:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    return result.scalar_one_or_none()


async def list_datasets(db: AsyncSession) -> list[Dataset]:
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    return list(result.scalars().all())


async def delete_dataset(dataset_id: str, db: AsyncSession) -> bool:
    ds = await get_dataset(dataset_id, db)
    if not ds:
        return False
    # Remove file
    try:
        Path(ds.file_path).unlink(missing_ok=True)
    except Exception as e:
        logger.warning("Could not delete file %s: %s", ds.file_path, e)
    await db.delete(ds)
    await db.commit()
    return True


async def get_dataset_preview(dataset_id: str, db: AsyncSession, n_rows: int = 50) -> dict[str, Any]:
    ds = await get_dataset(dataset_id, db)
    if not ds:
        raise ValueError(f"Dataset {dataset_id} not found")
    df = load_dataframe(ds.file_path, ds.file_type)
    preview = df.head(n_rows)
    # Convert to JSON-safe records
    records = []
    for _, row in preview.iterrows():
        rec = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                rec[col] = None
            elif hasattr(val, "item"):
                rec[col] = val.item()
            else:
                rec[col] = val
        records.append(rec)
    return {
        "id": ds.id,
        "columns": df.columns.tolist(),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "preview_rows": records,
        "row_count": len(df),
        "column_count": len(df.columns),
    }


async def save_analysis(
    dataset_id: str,
    analysis_type: str,
    result: dict[str, Any],
    execution_time_ms: float,
    db: AsyncSession,
) -> Analysis:
    """Upsert an analysis record for a dataset."""
    # Check if one exists
    existing = await db.execute(
        select(Analysis).where(
            Analysis.dataset_id == dataset_id,
            Analysis.analysis_type == analysis_type,
        )
    )
    analysis = existing.scalar_one_or_none()
    if analysis:
        analysis.result = result
        analysis.status = "completed"
        analysis.execution_time_ms = execution_time_ms
    else:
        analysis = Analysis(
            dataset_id=dataset_id,
            analysis_type=analysis_type,
            result=result,
            status="completed",
            execution_time_ms=execution_time_ms,
        )
        db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


async def get_analysis(dataset_id: str, analysis_type: str, db: AsyncSession) -> Analysis | None:
    result = await db.execute(
        select(Analysis).where(
            Analysis.dataset_id == dataset_id,
            Analysis.analysis_type == analysis_type,
        )
    )
    return result.scalar_one_or_none()
