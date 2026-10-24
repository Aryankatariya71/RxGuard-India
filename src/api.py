"""FastAPI service wrapping pipeline.analyze."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.patient import Patient
from src.pipeline import analyze

app = FastAPI(
    title="RxGuard India API",
    description="Deterministic prescription safety checker for Indian brand medicines.",
    version="0.1.0",
)


class PatientIn(BaseModel):
    age_years: float = Field(..., ge=0, le=120)
    weight_kg: float | None = Field(None, ge=0, le=400)
    sex: str | None = None
    creatinine_mg_dl: float | None = None
    egfr: float | None = None
    pregnant: bool | None = None
    conditions: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    prescription_text: str
    patient: PatientIn


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze_endpoint(body: AnalyzeRequest) -> dict[str, Any]:
    p = body.patient
    patient = Patient(
        age_years=p.age_years,
        weight_kg=p.weight_kg,
        sex=p.sex,
        creatinine_mg_dl=p.creatinine_mg_dl,
        egfr=p.egfr,
        pregnant=p.pregnant,
        conditions=list(p.conditions or []),
    )
    return analyze(body.prescription_text, patient)
