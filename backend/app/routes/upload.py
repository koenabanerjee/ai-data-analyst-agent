"""
app/routes/upload.py — file upload endpoint
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import Dataset, get_db
from app.models.schemas import DatasetUploadResponse
from app.services.dataset_service import save_uploaded_file
from app.utils.logging import get_logger

router = APIRouter(prefix="/upload", tags=["upload"])
logger = get_logger(__name__)
settings = get_settings()

ALLOWED_TYPES = {
    "text/csv": "csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xlsx",
    "application/octet-stream": None,  # sniff by extension
}
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV or XLSX file for analysis.
    - Validates file type and size
    - Detects duplicates via SHA-256
    - Returns dataset metadata immediately
    """
    # ── Validate extension ────────────────────────────────────────────────────
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: .csv, .xlsx",
        )
    file_type = "csv" if suffix == ".csv" else "xlsx"

    # ── Read and size-check ───────────────────────────────────────────────────
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB.",
        )

    # ── Duplicate detection ───────────────────────────────────────────────────
    sha = hashlib.sha256(content).hexdigest()
    # Store hash in schema_info — check existing datasets
    existing = await db.execute(select(Dataset))
    all_ds = existing.scalars().all()
    for ds in all_ds:
        if ds.schema_info.get("file_hash") == sha:
            # Return existing dataset instead of re-uploading
            logger.info("Duplicate upload detected, returning existing dataset %s", ds.id)
            return DatasetUploadResponse(
                id=ds.id,
                filename=ds.filename,
                original_filename=ds.original_filename,
                file_size=ds.file_size,
                file_type=ds.file_type,
                row_count=ds.row_count,
                column_count=ds.column_count,
                schema_info=ds.schema_info,
                status="ready",
                created_at=ds.created_at,
            )

    # ── Save and parse ────────────────────────────────────────────────────────
    try:
        dataset = await save_uploaded_file(content, file.filename or "upload", file_type, db)
        # Attach hash for future dedup
        dataset.schema_info = {**dataset.schema_info, "file_hash": sha}
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Upload failed for %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {exc}")

    return DatasetUploadResponse(
        id=dataset.id,
        filename=dataset.filename,
        original_filename=dataset.original_filename,
        file_size=dataset.file_size,
        file_type=dataset.file_type,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        schema_info=dataset.schema_info,
        status=dataset.status,
        created_at=dataset.created_at,
    )
