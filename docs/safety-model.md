# Safety model

## Principles

1. Decision-support only — never final medical authority.
2. No “prescription safe” badge. Empty findings → **No configured rule matched**.
3. Synthetic rules: `is_synthetic=true`, `evidence_status=DEMO_ONLY`, labeled in UI/export.
4. Exact brand resolve only — no silent fuzzy ingredient assignment.
5. Combination products expand to multiple ingredients.
6. Unresolved products remain visible; excluded from definitive duplicate matching.
7. Dosage checks only when a configured rule + required inputs exist.
8. Every finding carries rule id/version, evidence status, limitations, next step.
9. Mandatory disclaimer on app and reports.

## Severity

`CRITICAL | HIGH | MODERATE | LOW | INFORMATIONAL | UNKNOWN` — assigned only by configured rules.

## Evidence status

`DEMO_ONLY | REVIEWED_SOURCE | INCOMPLETE_EVIDENCE | NOT_EVALUATED`
