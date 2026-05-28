"""
app/routes/analysis.py — trigger and retrieve EDA analysis via LangGraph agent workflow
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import AgentState, build_eda_graph
from app.models.database import get_db
from app.models.schemas import EDAResult, StatusResponse, VisualisationResult
from app.services.dataset_service import (
    get_analysis,
    get_dataset,
    save_analysis,
)
from app.utils.data_utils import load_dataframe
from app.utils.logging import get_logger

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = get_logger(__name__)


async def _run_eda(dataset_id: str, db: AsyncSession) -> dict[str, Any]:
    """Core: compile and run the LangGraph EDA workflow."""
    ds = await get_dataset(dataset_id, db)
    if not ds:
        raise ValueError(f"Dataset {dataset_id} not found")

    df = load_dataframe(ds.file_path, ds.file_type)

    initial_state: AgentState = {
        "dataset_id": dataset_id,
        "df": df,
        "file_type": ds.file_type,
        "original_filename": ds.original_filename,
        "errors": [],
        "agent_trace": [],
    }

    graph = build_eda_graph()
    compiled = graph.compile()

    t0 = time.monotonic()
    final_state: AgentState = await compiled.ainvoke(initial_state)
    elapsed_ms = (time.monotonic() - t0) * 1000

    result = {
        "overview": final_state.get("overview", {}),
        "column_stats": final_state.get("column_stats", []),
        "missing_recommendations": final_state.get("missing_recommendations", []),
        "outlier_summary": final_state.get("outlier_summary", {}),
        "correlation": final_state.get("correlation", {}),
        "ai_insights": final_state.get("ai_insights", ""),
        "charts": final_state.get("charts", []),
        "report_sections": final_state.get("report_sections", {}),
        "agent_trace": final_state.get("agent_trace", []),
        "errors": final_state.get("errors", []),
    }
    return result, elapsed_ms


@router.post("/{dataset_id}/run", response_model=StatusResponse)
async def trigger_analysis(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger full EDA in background. Use GET /eda to retrieve results.
    """
    ds = await get_dataset(dataset_id, db)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    background_tasks.add_task(_background_eda, dataset_id)
    return StatusResponse(status="processing", message="EDA pipeline started. Poll /eda for results.")


async def _background_eda(dataset_id: str):
    """Background task wrapper — needs its own DB session."""
    from app.models.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            result, elapsed = await _run_eda(dataset_id, db)
            await save_analysis(dataset_id, "full_eda", result, elapsed, db)
            logger.info("Background EDA complete for %s in %.0fms", dataset_id, elapsed)
        except Exception as exc:
            logger.exception("Background EDA failed for %s", dataset_id)


@router.post("/{dataset_id}/run-sync")
async def trigger_analysis_sync(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Run EDA synchronously and return the full result.
    Slower but simpler for smaller datasets.
    """
    ds = await get_dataset(dataset_id, db)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        result, elapsed = await _run_eda(dataset_id, db)
        await save_analysis(dataset_id, "full_eda", result, elapsed, db)
        return {"dataset_id": dataset_id, "elapsed_ms": round(elapsed), **result}
    except Exception as exc:
        logger.exception("Sync EDA failed for %s", dataset_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{dataset_id}/eda")
async def get_eda(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve cached EDA result for a dataset."""
    analysis = await get_analysis(dataset_id, "full_eda", db)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="EDA not found. Run POST /analysis/{dataset_id}/run-sync first.",
        )
    return {"dataset_id": dataset_id, "status": analysis.status, **analysis.result}


@router.get("/{dataset_id}/visualizations")
async def get_visualizations(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Return just the charts from the cached EDA."""
    analysis = await get_analysis(dataset_id, "full_eda", db)
    if not analysis:
        raise HTTPException(status_code=404, detail="Run EDA first.")
    charts = analysis.result.get("charts", [])
    return {"dataset_id": dataset_id, "charts": charts, "count": len(charts)}


@router.get("/{dataset_id}/insights")
async def get_insights(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Return just the AI insights from the cached EDA."""
    analysis = await get_analysis(dataset_id, "full_eda", db)
    if not analysis:
        raise HTTPException(status_code=404, detail="Run EDA first.")
    return {
        "dataset_id": dataset_id,
        "ai_insights": analysis.result.get("ai_insights", ""),
        "correlation": analysis.result.get("correlation", {}),
        "outlier_summary": analysis.result.get("outlier_summary", {}),
    }
