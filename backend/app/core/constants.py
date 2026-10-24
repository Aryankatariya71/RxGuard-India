"""Shared enumerations and safety copy."""

SAFETY_DISCLAIMER = (
    "RxGuard India is a prescription-review support prototype. It does not replace a "
    "doctor or pharmacist. A missing alert does not prove a prescription is safe. "
    "Verify findings with a qualified healthcare professional."
)

SHORT_DISCLAIMER = (
    "Decision-support prototype only. A missing alert does not prove safety. "
    "Consult a qualified clinician."
)

# Summary status — NEVER "safe" / "clear" / "no issues"
SUMMARY_STATUSES = (
    "Review recommended",
    "Potential findings",
    "Assessment incomplete",
)

RULE_STATUSES = (
    "DEMO_ILLUSTRATIVE",
    "REVIEW_PENDING",
    "CLINICALLY_REVIEWED",
)

IDENTITY_STATUSES = (
    "VERIFIED_CATALOGUE_MATCH",
    "USER_CONFIRMED_MATCH",
    "SUGGESTED_MATCH",
    "AMBIGUOUS",
    "UNRESOLVED",
)

SEVERITIES = (
    "CRITICAL",
    "HIGH",
    "MODERATE",
    "LOW",
    "INFORMATIONAL",
    "UNKNOWN",
)

FINDING_TYPES = (
    "DUPLICATE_INGREDIENT",
    "INTERACTION_RULE_MATCH",
    "DOSE_RULE_MATCH",
    "PRODUCT_UNRESOLVED",
    "CHECK_NOT_RUN",
    "DATA_QUALITY_NOTICE",
)

CATALOGUE_SOURCE_LABEL = (
    "A-Z Medicines Dataset of India (Kaggle), unverified"
)
DDINTER_SOURCE_LABEL = "DDInter 2.0 (academic use)"


def map_legacy_rule_status(
    *,
    status: str | None,
    verified_by_pharmacist: bool = False,
    is_synthetic: bool = False,
) -> str:
    """Map existing DRAFT / demo flags to Stage-1 rule statuses."""
    if verified_by_pharmacist:
        return "CLINICALLY_REVIEWED"
    if is_synthetic:
        return "DEMO_ILLUSTRATIVE"
    raw = (status or "").upper()
    if raw in {"DEMO", "DEMO_ONLY", "DEMO_ILLUSTRATIVE", "SYNTHETIC"}:
        return "DEMO_ILLUSTRATIVE"
    if raw in {"REVIEWED", "CLINICALLY_REVIEWED", "VERIFIED"}:
        return "CLINICALLY_REVIEWED"
    # DRAFT curated / dose / DDInter-derived → REVIEW_PENDING
    return "REVIEW_PENDING"
