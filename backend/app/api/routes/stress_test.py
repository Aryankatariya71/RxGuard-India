"""Stress-test synthetic prescriptions (in-memory)."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.stress_test import ALLOWED_N, DEFAULT_N, MAX_N, run_stress_test

router = APIRouter(tags=["stress-test"])


class StressTestBody(BaseModel):
    n: int = Field(DEFAULT_N, ge=1, le=MAX_N)
    seed: int | None = None


@router.post("/stress-test")
def post_stress_test(
    body: StressTestBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Run N synthetic prescriptions through engines without persisting.

    Cap is 2000. Preferred sizes: 100 / 500 / 1000 / 2000.
    BackgroundTasks is accepted so the framework can schedule cleanup; the
    batch itself runs in-process in chunks for deterministic timing metrics.
    """
    _ = background_tasks  # reserved for future async job queue
    n = body.n if body.n in ALLOWED_N else min(ALLOWED_N, key=lambda x: abs(x - body.n))
    return run_stress_test(db, n=n, seed=body.seed)
