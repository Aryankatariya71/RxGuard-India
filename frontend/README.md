# RxGuard India — Frontend

Premium Vite + React + TypeScript UI for the deterministic prescription safety engine.

## Stack

- Vite, React 19, TypeScript
- Tailwind CSS v4
- framer-motion, recharts (available), lucide-react

## Develop

```bash
# from repo root — API + UI together
../run_demo.sh

# or frontend only (falls back to bundled mock responses)
npm install
npm run dev
```

UI: http://localhost:5173  
API (proxied as `/api`): http://127.0.0.1:8000

## API contract

`POST /api/analyze` body:

```json
{
  "prescription_text": "Tab Dolo 650 TDS",
  "patient": {
    "age_years": 35,
    "weight_kg": 70,
    "sex": "M",
    "egfr": 90,
    "pregnant": false
  }
}
```

Response fields used: `items`, `daily_doses`, `alerts`, `counts`, `verdict`, `needs_confirmation`.

If the API is unreachable, example scenarios use `src/data/mock_responses.json` (labelled **offline demo data**).

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Vite on :5173 with `/api` proxy |
| `npm run build` | Production build |
| `npm run preview` | Preview build |

## Notes

- Dark theme default; toggle in navbar.
- Print/PDF via browser print + print stylesheet.
- Streamlit `app.py` remains untouched as a fallback.
