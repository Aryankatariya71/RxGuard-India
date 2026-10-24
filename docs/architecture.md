# Architecture — RxGuard India (HM-02)

## Layers

1. **UI** (`frontend/`) — React Router pages call typed API client (`src/api/hm02.ts`).
2. **API** (`backend/app/api/routes/`) — FastAPI routers, Pydantic validation.
3. **Services** — catalogue search, ingredient resolution, duplicate / interaction / dosage engines, review orchestration, demo scenarios.
4. **Persistence** — SQLAlchemy models → SQLite (default) or Postgres.

## Review evaluation pipeline

`evaluate_prescription(review_id)`:

1. Load prescription + items + products/ingredients
2. Resolve status per item (exact catalogue ID or unresolved)
3. Duplicate ingredient detection (canonical IDs only)
4. Interaction pair matching against active rules
5. Dosage rule evaluation when inputs present; else `NOT_EVALUATED` / `INSUFFICIENT_DATA`
6. Persist findings with rule + catalogue versions
7. Return structured report

## Safety model principles

See `docs/safety-model.md`. Engines never invent ingredients or claim “safe.”
