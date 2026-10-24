# RxGuard India — 2-minute demo script

Open the Streamlit app (`streamlit run app.py`). Click each example chip (or paste the text). Patient age/weight are set by the chip.

---

## 1. Warfarin + aspirin + ibuprofen (~25s)

**Patient:** age 55, weight 70 kg  

**Prescription:**
```
Tab Warf 5 1-0-0
Tab Ecosprin 75 OD
Tab Brufen 400 TDS
```

**Say:** Three critical interaction alerts — warfarin with each NSAID, plus aspirin with ibuprofen. Rules are curated drafts with source URLs, not an LLM guess.

**Expect:** 3 critical, 1 review (NSAID class duplicate).

---

## 2. Hidden paracetamol duplication (~20s)

**Patient:** age 35, weight 70 kg  

**Prescription:**
```
Tab Dolo 650 1-0-1 x 5 days
Tab Crocin Advance BD
Tab Combiflam 1-0-1
```

**Say:** Same API across three brands, including a combination product. Total stays under the adult draft limit, so this is review — not critical.

**Expect:** 0 critical, 1 review.

---

## 3. Child overdose (~20s)

**Patient:** age 5, weight 18 kg  

**Prescription:**
```
Tab Dolo 650 TDS
Tab Crocin Advance BD
```

**Say:** Pediatric limit is weight × mg/kg. Reason shows `18 kg x 60 mg/kg = 1080 mg/day`. We never invent a weight.

**Expect:** 1 critical (merged duplicate + dose).

---

## 4. Misspelling + unknown brand (~15s)

**Patient:** age 35, weight 70 kg  

**Prescription:**
```
Tab Dolo650 TDS
Tab Pantap 40 OD
Tab Xyzabc 1-0-1
```

**Say:** Fuzzy resolve recovers Dolo/Pantop; unknown brand is never skipped — it becomes a confirm-brand alert with candidates when available.

**Expect:** needs_confirmation for Xyzabc; no crash.

---

## 5. Kidney patient on NSAID (~20s)

**Patient:** age 55, weight 70 kg, eGFR 10 (set via API or temporarily in code/patient fields if exposed)  

**Prescription:**
```
Tab Brufen 400 TDS
```

**API alternative:**
```bash
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"prescription_text":"Tab Brufen 400 TDS","patient":{"age_years":55,"weight_kg":70,"egfr":10}}'
```

**Say:** Draft max-dose rule marks severe / kidney-failure NSAID use as avoid → critical renal alert.

**Expect:** 1 critical dose/renal alert.

---

## 6. Clean prescription (~10s)

**Patient:** age 40, weight 70 kg  

**Prescription:**
```
Tab Pantop 40 OD
Tab Amlong 5 OD
```

**Say:** Resolved brands, daily totals under limits, no critical alerts — verdict clear.

**Expect:** 0 critical.

---

**Close:** All numbers are DRAFT pending pharmacist verification. See `docs/PHARMACIST_REVIEW.md` and `docs/EVAL_REPORT.md`.
