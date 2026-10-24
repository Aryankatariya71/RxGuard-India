# RxGuard India — Methodology

> RxGuard India is a prescription-review support prototype. It does not replace a doctor or pharmacist. A missing alert does not prove a prescription is safe. Verify findings with a qualified healthcare professional.

This document mirrors the in-app **Methodology** page (`/methodology`). Live counts (catalogue size, rule totals, evaluation figures, test counts) are served by `GET /api/methodology/stats`, `GET /api/meta`, and `GET /api/evaluation`. Do not hard-code those numbers in the UI.

## Methodology at a glance

- Deterministic rules engine — not an LLM judge.
- Local medicine catalogue with brand → ingredient expansion.
- Duplicate, dose, and interaction checks with cited draft rules.
- Uncertainty is shown (checks not run, unresolved identity).
- Developer-labeled gold evaluation measures internal consistency, not clinical accuracy.
- Automated backend tests guard parsing, engines, and API contracts.

## 1. The problem

Indian prescriptions use brand names, combination products, and abbreviations (OD, BD, TDS, SOS) that can hide duplicate ingredients, interactions, and excessive doses.

| Challenge | How we address it |
|---|---|
| Misspelled brands | Normalisation + exact / prefix / fuzzy resolution with confirmation |
| Combination ingredients | Expand brands into APIs + strengths before checks |
| Patient-specific dose limits | Sum mg/day; apply draft adult / paediatric / renal rules when data exists |
| Alert fatigue | Merge duplicate+dose, dedupe pairs, tier critical / review / info |

## 2. Design principles

- Deterministic rules engine, not an LLM judge.
- Every finding traces to a stored rule (id, source, version, status).
- Uncertainty is shown, not hidden.
- Unresolved items block dependent checks.
- Identity confidence and clinical severity are separate.
- “No match” never means a prescription needs no review.

## 3. Pipeline

Prescription text → Parser → Brand resolver → Ingredient expansion → Daily dose → Duplicate / Interaction / Dose checks → Alert manager → Report.

Worked live example (via `POST /api/analyze`):

```
Tab Dolo 650 1-0-1 x 5 days
Tab Combiflam 1-0-1
```

## 4. Data sources

| Source | Licence / terms | What we use | What we do not trust it for |
|---|---|---|---|
| A–Z Medicines Dataset of India (Kaggle) | Respect upstream Kaggle licence | Brand ↔ composition catalogue (≤2 fields) | “Use” / “side effect” text; unverified 2022 prices; not CDSCO-verified |
| DDInter 2.0 | Academic / non-commercial | Pair levels after normalisation; Unknown dropped | Complete clinical interaction coverage |
| Curated draft rules | Project-authored, status-labeled | Priority pairs and dose limits | Anything not CLINICALLY_REVIEWED |
| Synthetic demo seed | DEMO_ONLY | Offline demos | Real formulary data |

Row counts before/after cleaning and DDInter pair totals come from the live stats API / generated file stats — not from this markdown.

## 5. Brand resolution

Normalisation (case, punctuation, letter/digit splits) → exact → token-prefix → fuzzy. Number-aware matching. Fuzzy matches are suggestions requiring confirmation (`GET /api/medicines/search`).

## 6. Ingredient expansion

Parse compositions into (ingredient, strength, unit, per-unit); salt stripping and synonyms; protected names; per-5-ml syrup handling when known. Source limitation: at most two compositions per product — 3+ ingredient products may be incomplete.

## 7. Prescription parsing and dose calculation

Frequencies: OD, BD, TDS, QID, HS, 1-0-1 patterns, SOS (assumed maximum, labeled). Daily dose summed per ingredient. Ambiguous schedules → CHECK_NOT_RUN.

`daily_mg(ingredient) = Σ (strength_mg_per_unit × units_per_day)`

## 8. Safety checks

- Duplicate ingredient (and class where configured).
- Interaction (unordered pairs; curated overrides DDInter; class rules; Major/Moderate/Minor → critical/review/info).
- Dose (adult, paediatric mg/kg, renal band, elderly note; unable to assess when fields missing).

Rule status lifecycle: `DEMO_ILLUSTRATIVE` → `REVIEW_PENDING` → `CLINICALLY_REVIEWED`. Live counts per status come from the API. Today most rules are REVIEW_PENDING.

## 9. Alert-fatigue design

Merge duplicate + dose for the same ingredient; dedupe; three tiers; collapsed info. Naive vs merged counts: measure via the stress-test page / API when available.

## 10. Evaluation

Developer-labeled gold set in `tests/gold_prescriptions.json`. Metrics (brand-resolution accuracy, precision/recall by finding type, false-alarm rate on clean prescriptions) from `docs/EVAL_REPORT.md` via `GET /api/evaluation`.

**Callout:** Labels were written by the development team from the same rule set, so these figures show internal consistency, not clinical accuracy. Pharmacist verification is the next step.

## 11. Explainability and uncertainty

Findings expose rule id, numbers used, source, version, status. Checks-not-run panel when data is insufficient. Identity statuses: VERIFIED_CATALOGUE_MATCH, USER_CONFIRMED_MATCH, SUGGESTED_MATCH, AMBIGUOUS, UNRESOLVED.

## 12. Privacy and security

Synthetic data by default; no names/phone/Aadhaar; no prescription logging by default; offline-capable; no external LLM/OCR by default (browser speech needs network; OCR is local); no secrets in code.

## 13. Limitations and next steps

Rules pending pharmacist review; 3+ ingredient products not fully representable; syrup basis sometimes unknown; 2022 unverified prices; pairwise interactions only; limited allergy/pregnancy coverage; not a medical device.

Next (no timelines): pharmacist review workflow, verified formulary data, more rules, hospital pilot with clinical oversight.

## 14. Related work and references

Related: RxCheck-style checkers; PillChecker-style product lookup. Differences: brand-level splitting, patient-aware draft dose limits, alert tiers, checks-not-run, labeled evaluation pending pharmacist verification.

Credits: DDInter; A–Z Medicines Dataset of India (Kaggle) authors.

### How to reproduce

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
python evaluate.py
uvicorn backend.app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

Regenerate methodology build meta (test counts / file stats):

```bash
python backend/scripts/generate_methodology_meta.py
```

---

RxGuard India is a prescription-review support prototype. It does not replace a doctor or pharmacist. A missing alert does not prove a prescription is safe. Verify findings with a qualified healthcare professional.
