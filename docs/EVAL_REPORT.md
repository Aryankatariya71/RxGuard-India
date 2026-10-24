# Evaluation report

> **developer-labeled, pending pharmacist verification; entries with `verified_by` set are reported separately**

- Cases: 40 (developer-labeled: 40, pharmacist-verified: 0)
- Brand-resolution accuracy: 1.0 (65/65)
- False-alarm rate on clean prescriptions (any critical): 0.0 (0/5)
- Average alerts per prescription: 0.975

## Precision / recall by alert type

| type | precision | recall | tp | fp | fn |
|---|---|---|---|---|---|
| dose | 1.0 | 1.0 | 5 | 0 | 0 |
| duplicate | 1.0 | 1.0 | 8 | 0 | 0 |
| duplicate_dose | 1.0 | 1.0 | 3 | 0 | 0 |
| interaction | 1.0 | 1.0 | 12 | 0 | 0 |
| needs_confirmation | 1.0 | 1.0 | 5 | 0 | 0 |
| strength_unclear | 1.0 | 1.0 | 2 | 0 | 0 |

## Failed cases (developer-labeled)

_None._
## Failed cases (pharmacist-verified subset)

_None (no verified_by entries yet, or all passed)._
