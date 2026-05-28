"""
app/routes/datasets.py — CRUD for datasets
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.schemas import DatasetListItem, DatasetPreview
from app.services.dataset_service import delete_dataset, get_dataset_preview, list_datasets
from app.utils.logging import get_logger

router = APIRouter(prefix="/datasets", tags=["datasets"])
logger = get_logger(__name__)


@router.get("", response_model=list[DatasetListItem])
async def get_all_datasets(db: AsyncSession = Depends(get_db)):
    datasets = await list_datasets(db)
    return [
        DatasetListItem(
            id=ds.id,
            original_filename=ds.original_filename,
            file_size=ds.file_size,
            file_type=ds.file_type,
            row_count=ds.row_count,
            column_count=ds.column_count,
            status=ds.status,
            created_at=ds.created_at,
        )
        for ds in datasets
    ]


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
async def preview_dataset(
    dataset_id: str,
    n_rows: int = 50,
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_dataset_preview(dataset_id, db, n_rows)
        return DatasetPreview(**data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Preview failed for %s", dataset_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{dataset_id}")
async def remove_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await delete_dataset(dataset_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return {"status": "deleted", "dataset_id": dataset_id}
