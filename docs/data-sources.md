# Medicine data sources

## What is wired today

| Source | Access | Coverage | Status in RxGuard |
|---|---|---|---|
| **RxNorm (NLM RxNav REST)** | Free public HTTP API, no API key | US clinical drug terminology (RXCUI, ingredients, related concepts) | Live search via `/api/external/rxnorm/search`; confirmed hits upserted locally as `SOURCE_BACKED` / `PARTIALLY_VERIFIED`, geography `US_RXNORM` |
| **A–Z Medicines Dataset of India (Kaggle)** | Local `data/brands_clean.parquet` derived from public Kaggle CSV | ~250k Indian retail brand rows with ≤2 composition fields | Import via `python backend/scripts/seed_demo_data.py --catalogue` (set `DEMO_MODE=false`). Labeled `PARTIALLY_VERIFIED`, geography `INDIA_CATALOGUE`. **Not** CDSCO-verified. |
| **Synthetic demo seed** | Bundled JSON | Demo Product Alpha/Beta/Gamma/Delta | `DEMO_ONLY` |

## CDSCO (https://cdsco.gov.in/)

Investigated for machine-readable bulk medicine catalogues:

- CDSCO Data Bank mainly publishes **PDFs** (NLEM lists, manufacturer/license lists, approved new drugs lists) — not a documented public JSON/CSV bulk API for retail brand↔ingredient mappings.
- Drugs@CDSCO / SUGAM portals are interactive regulatory systems; **no free documented bulk download API** suitable for this prototype was found.
- Third-party commercial APIs (e.g. DrugSetu) require API keys and are **out of scope** (no paid APIs).

**Honest limitation:** RxGuard does **not** claim a complete CDSCO-backed Indian brand catalogue. Indian retail coverage, when imported, comes from the unverified Kaggle A–Z dataset already in this repo. RxNorm does **not** replace an Indian brand formulary.

## Clinical rules

Interaction and dosage rules remain largely `DEMO_ILLUSTRATIVE` / `REVIEW_PENDING`. Retrieving a real RxNorm product does **not** validate synthetic demo rules. Missing applicable rules → `NOT_EVALUATED` / “No matching rule in this prototype dataset”.

## Licences / attribution

- RxNorm: NLM RxNav Terms of Service; non-proprietary RxNorm vocabulary.
- Kaggle A–Z Medicines Dataset of India: respect upstream Kaggle licence; do not redistribute raw DDInter CSVs commercially.
- CDSCO PDFs: government publications; not bulk-imported here.
