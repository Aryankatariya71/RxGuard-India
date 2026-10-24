"""RxGuard India HM-02 FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import (
    analyze_legacy,
    external,
    health,
    medicines,
    reviews,
    stress_test,
)
from backend.app.core.config import get_settings
from backend.app.db.session import Base, engine
from backend.app.models import entities  # noqa: F401 — register models

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("rxguard")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from backend.app.db.migrate import upgrade

    upgrade()
    logger.info("Database schema ensured")
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "HM-02 Prescription Safety Checker prototype. "
        "Decision-support only. Synthetic demo data is labeled DEMO_ONLY."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = FastAPI()  # unused — mount routes on app with /api prefix via include


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


app.include_router(health.router, prefix="/api")
app.include_router(analyze_legacy.router, prefix="/api")
app.include_router(medicines.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(external.router, prefix="/api")
app.include_router(stress_test.router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "note": "Prototype — not clinically validated",
    }
