"""
app/routes/query.py — natural language query endpoint
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import query_agent
from app.models.database import QueryLog, get_db
from app.models.schemas import QueryRequest, QueryResponse
from app.services.dataset_service import get_analysis, get_dataset
from app.utils.data_utils import load_dataframe
from app.utils.logging import get_logger

router = APIRouter(prefix="/query", tags=["query"])
logger = get_logger(__name__)


@router.post("/{dataset_id}", response_model=QueryResponse)
async def ask_question(
    dataset_id: str,
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask any natural language question about the dataset.
    The Query Agent interprets intent, analyses the data, and returns
    a human-like answer + optional chart.
    """
    ds = await get_dataset(dataset_id, db)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Load EDA context (soft fail — query agent can still work without it)
    analysis = await get_analysis(dataset_id, "full_eda", db)
    eda_result = analysis.result if analysis else {}

    # Load dataframe
    try:
        df = load_dataframe(ds.file_path, ds.file_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {exc}")

    # Run query agent
    try:
        result = await query_agent(df, body.question, eda_result)
    except Exception as exc:
        logger.exception("Query agent failed for dataset %s", dataset_id)
        raise HTTPException(status_code=500, detail=str(exc))

    # Persist query log
    log = QueryLog(
        id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        question=body.question,
        answer=result["answer"],
        chart_json=result.get("chart"),
        agent_trace=result.get("agent_trace", {}),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return QueryResponse(
        id=log.id,
        dataset_id=dataset_id,
        question=body.question,
        answer=log.answer,
        chart=log.chart_json,
        agent_trace=log.agent_trace,
        created_at=log.created_at,
    )


@router.get("/{dataset_id}/history")
async def query_history(dataset_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(QueryLog)
        .where(QueryLog.dataset_id == dataset_id)
        .order_by(QueryLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "question": log.question,
            "answer": log.answer,
            "has_chart": log.chart_json is not None,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
