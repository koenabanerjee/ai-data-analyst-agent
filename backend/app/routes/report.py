"""
app/routes/report.py — PDF report generation and download
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Report, get_db
from app.models.schemas import ReportResponse
from app.services.dataset_service import get_analysis, get_dataset
from app.services.report_service import generate_pdf_report
from app.utils.logging import get_logger

router = APIRouter(prefix="/report", tags=["report"])
logger = get_logger(__name__)


@router.post("/{dataset_id}/generate", response_model=ReportResponse)
async def generate_report(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Generate a professional PDF report for the dataset."""
    ds = await get_dataset(dataset_id, db)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    analysis = await get_analysis(dataset_id, "full_eda", db)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="EDA not found. Run POST /analysis/{dataset_id}/run-sync first.",
        )

    sections = analysis.result.get("report_sections", {})
    if not sections:
        # fallback — build from analysis result directly
        sections = {
            "dataset_name": ds.original_filename,
            **{k: analysis.result.get(k, {}) for k in
               ["overview", "column_stats", "missing_recommendations", "outlier_summary", "correlation", "ai_insights", "charts"]},
        }

    try:
        pdf_path = await generate_pdf_report(sections, dataset_id)
    except Exception as exc:
        logger.exception("PDF generation failed for %s", dataset_id)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    file_size = Path(pdf_path).stat().st_size

    report = Report(
        id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        file_path=pdf_path,
        file_size=file_size,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportResponse(
        id=report.id,
        dataset_id=dataset_id,
        file_path=pdf_path,
        file_size=file_size,
        created_at=report.created_at,
    )


@router.get("/{dataset_id}/download")
async def download_report(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Download the latest PDF report for a dataset."""
    from sqlalchemy import select
    result = await db.execute(
        select(Report)
        .where(Report.dataset_id == dataset_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="No report found. Generate one first.")

    path = Path(report.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    ds = await get_dataset(dataset_id, db)
    safe_name = f"report_{ds.original_filename.rsplit('.', 1)[0] if ds else dataset_id}.pdf"

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=safe_name,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
