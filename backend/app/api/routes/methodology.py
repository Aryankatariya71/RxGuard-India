"""Methodology / meta / evaluation endpoints — live counts only."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.methodology_stats import (
    build_evaluation,
    build_meta,
    build_methodology_stats,
)

router = APIRouter(tags=["methodology"])


@router.get("/methodology/stats")
def methodology_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Real catalogue / rules / evaluation counts for the Methodology page."""
    return build_methodology_stats(db)


@router.get("/meta")
def meta(db: Session = Depends(get_db)) -> dict[str, Any]:
    return build_meta(db)


@router.get("/evaluation")
def evaluation(db: Session = Depends(get_db)) -> dict[str, Any]:
    return build_evaluation(db)
