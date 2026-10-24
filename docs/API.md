# RxGuard India API

Deterministic rules engine — not an LLM judge. Every alert cites a rule id / source.

## Run

```bash
source venv/bin/activate
uvicorn src.api:app --reload --port 8000
```

Open interactive docs at `http://127.0.0.1:8000/docs`.

## Endpoints

### `GET /health`

Returns `{"status": "ok"}`.

### `POST /analyze`

**Request body**

```json
{
  "prescription_text": "Tab Dolo 650 TDS\nTab Crocin Advance BD",
  "patient": {
    "age_years": 35,
    "weight_kg": 70,
    "sex": "M",
    "egfr": null,
    "creatinine_mg_dl": null
  }
}
```

**Response (summary)**

| Field | Meaning |
|---|---|
| `items` | Per-line resolve status, matched brand, ingredients |
| `daily_doses` | `by_ingredient` totals + `strength_unclear` |
| `alerts` | Merged alerts `{id, type, tier, title, reason, suggested_action, ingredients, brands, source_rule_id, source_label}` |
| `counts` | `{critical, review, info}` |
| `verdict` | `action_needed` \| `review` \| `clear` |
| `needs_confirmation` | Ambiguous / not-found brands (never silently skipped) |

## Example

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"prescription_text":"Tab Warf 5 1-0-0\nTab Ecosprin 75 OD\nTab Brufen 400 TDS","patient":{"age_years":55,"weight_kg":70}}'
```
