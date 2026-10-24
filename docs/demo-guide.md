# Demo guide

## Quick start

```bash
./run_demo.sh
```

Open http://localhost:5173 → **New Prescription Review** → load a scenario.

## Scenarios

| Button | Demonstrates |
|---|---|
| Duplicate ingredient | Same Ingredient-Demo across two brands |
| Interaction | SYN-INT rule between two demo ingredients |
| Missing dosage info | Dosage rule skipped → NOT_EVALUATED |
| Unresolved brand | Unknown product stays unresolved |
| Combination product | Multi-ingredient product + duplicate path |

## Talking points

- Every finding shows DEMO_ONLY / Demonstration rule labeling
- Report never says “safe”
- Export includes full disclaimer
- Settings shows `auth_enabled: false` and demo-data mode
