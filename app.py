"""RxGuard India — Streamlit UI (clinical logic lives in src/)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

import ui_style as ui
from src.daily_dose import daily_dose_by_ingredient, resolve_prescription
from src.patient import Patient
from src.rx_parser import parse_prescription

st.set_page_config(
    page_title="RxGuard India",
    page_icon="💊",
    layout="wide",
)

# Existing examples preserved; chip labels may be shorter aliases.
EXAMPLES: dict[str, dict] = {
    "Hidden paracetamol duplication": {
        "rx": (
            "Tab Dolo 650 1-0-1 x 5 days\n"
            "Tab Crocin Advance BD\n"
            "Tab Combiflam 1-0-1"
        ),
        "age": 35.0,
        "weight": 70.0,
    },
    "Overdose": {
        "rx": (
            "Tab Dolo 650 1-1-1-1\n"
            "Tab Crocin Advance QID\n"
            "Tab Combiflam 1-1-1"
        ),
        "age": 35.0,
        "weight": 70.0,
    },
    "Child overdose": {
        "rx": ("Tab Dolo 650 TDS\n" "Tab Crocin Advance BD"),
        "age": 5.0,
        "weight": 18.0,
    },
    "Misspelling + unknown brand": {
        "rx": ("Tab Dolo650 TDS\n" "Tab Pantap 40 OD\n" "Tab Xyzabc 1-0-1"),
        "age": 35.0,
        "weight": 70.0,
    },
    "Warfarin + Aspirin + Ibuprofen": {
        "rx": ("Tab Warf 5 1-0-0\n" "Tab Ecosprin 75 OD\n" "Tab Brufen 400 TDS"),
        "age": 55.0,
        "weight": 70.0,
    },
    "Augmentin + Pantop + Ascoril LS": {
        "rx": (
            "Tab Augmentin 625 Duo 1-0-1 x 5 days\n"
            "Tab Pantop 40 OD AC\n"
            "Syp Ascoril LS 5ml TDS"
        ),
        "age": 35.0,
        "weight": 70.0,
    },
}

# Chip order in the input card (Overdose = former Adult overdose).
EXAMPLE_CHIPS = [
    "Hidden paracetamol duplication",
    "Overdose",
    "Child overdose",
    "Misspelling + unknown brand",
    "Warfarin + Aspirin + Ibuprofen",
    "Augmentin + Pantop + Ascoril LS",
]


def _format_strength(ing: dict) -> str:
    if ing.get("strength_missing") or ing.get("strength_value") is None:
        return "strength missing"
    val = ing["strength_value"]
    unit = ing.get("unit") or ""
    per_v = ing.get("per_value")
    per_u = ing.get("per_unit")
    if per_v is not None and per_u:
        return f"{ui.fmt_qty(val, unit)}/{ui.fmt_num(per_v)}{per_u}"
    if ing.get("per_unit_missing"):
        return f"{ui.fmt_qty(val, unit)} (per-unit unclear)"
    return ui.fmt_qty(val, unit)


def _ingredient_chips(ingredients: list[dict]) -> list[str]:
    chips = []
    for ing in ingredients or []:
        name = ing.get("ingredient") or "?"
        chips.append(f"{name} {_format_strength(ing)}")
    return chips


@st.cache_resource(show_spinner=False)
def warm_caches() -> str:
    """Preload brand index / DDInter / dose rules so Analyze stays snappy."""
    try:
        from src.resolver import resolve

        resolve("dolo 650")
    except Exception:
        pass
    try:
        from src.quick_interactions import major_pair_count

        major_pair_count()
    except Exception:
        pass
    try:
        from src.quick_dose import load_max_dose_rules

        load_max_dose_rules()
    except Exception:
        pass
    return "ready"


def _load_example(label: str) -> None:
    ex = EXAMPLES[label]
    st.session_state["rx_text"] = ex["rx"]
    st.session_state["patient_age"] = float(ex["age"])
    st.session_state["patient_weight"] = float(ex["weight"])
    # Clear previous results so user re-analyzes with the new example.
    st.session_state.pop("analysis", None)


def _collect_alerts(
    *,
    dose: dict,
    patient: Patient,
    resolved: list[dict],
) -> list[dict[str, Any]]:
    """Build unified alert cards from existing rule outputs (presentation only)."""
    alerts: list[dict[str, Any]] = []
    by_ing = dose.get("by_ingredient") or []

    # Duplicates
    for row in by_ing:
        brands = list(dict.fromkeys(c["brand"] for c in (row.get("contributions") or [])))
        if len(brands) >= 2:
            total_txt = ui.fmt_qty(row["total_mg_per_day"], row["unit"])
            brand_list = " and ".join(brands)
            alerts.append(
                {
                    "tier": "critical",
                    "icon": "⚠",
                    "title": f"Duplicate ingredient: {row['ingredient'].title()}",
                    "reason": (
                        f"{row['ingredient'].title()} is in {brand_list}. "
                        f"Combined total: {total_txt}/day."
                    ),
                    "action": "Confirm whether both brands are intentional; avoid stacking the same API.",
                    "rule": "Duplicate ingredient across brands",
                }
            )

    # Draft dose limits
    try:
        from src.quick_dose import check_doses

        for a in check_doses(dose, patient):
            tier = a.get("tier") or "info"
            title = {
                "critical": f"Dose limit exceeded: {(a.get('ingredient') or 'ingredient').title()}",
                "review": f"Dose near limit: {(a.get('ingredient') or 'ingredient').title()}",
                "info": "Pediatric dose check",
            }.get(tier, "Dose check")
            alerts.append(
                {
                    "tier": tier,
                    "icon": "⬆" if tier == "critical" else ("◎" if tier == "review" else "ℹ"),
                    "title": title,
                    "reason": a.get("reason") or "",
                    "action": "Confirm with prescriber. Draft rule, pending pharmacist verification.",
                    "rule": "Commonly cited label limit, DRAFT",
                }
            )
    except Exception:
        pass

    # Unclear strengths
    for u in dose.get("strength_unclear") or []:
        alerts.append(
            {
                "tier": "review",
                "icon": "?",
                "title": "Strength unclear, check label",
                "reason": (
                    f"{u.get('ingredient')} in {u.get('brand')} "
                    f"({u.get('reason')})."
                ),
                "action": "Read the pack label before calculating liquid dose.",
                "rule": "per_unit_missing / strength basis unknown",
            }
        )

    # DDInter Major
    try:
        from src.quick_interactions import check_major_interactions

        names: list[str] = []
        for item in resolved:
            for ing in item.get("ingredients") or []:
                if ing.get("ingredient"):
                    names.append(ing["ingredient"])
        for hit in check_major_interactions(names):
            a = str(hit["ing_a"]).title()
            b = str(hit["ing_b"]).title()
            alerts.append(
                {
                    "tier": "critical",
                    "icon": "⚠",
                    "title": f"Major interaction: {a} + {b}",
                    "reason": f"{a} + {b}: Major interaction per DDInter 2.0.",
                    "action": "Review with prescriber before dispensing.",
                    "rule": "DDInter 2.0 (academic use)",
                }
            )
    except Exception:
        pass

    return alerts


def _limit_for_ingredient(name: str, patient: Patient) -> float | None:
    try:
        from src.quick_dose import load_max_dose_rules

        rules = load_max_dose_rules()
        rule = rules.get(str(name).lower())
        if not rule:
            return None
        if float(patient.age_years) < 18:
            ped = rule.get("pediatric_mg_per_kg_day")
            if ped is None or not patient.weight_kg:
                return None
            return float(patient.weight_kg) * float(ped)
        adult = rule.get("adult_max_mg_day")
        return float(adult) if adult is not None else None
    except Exception:
        return None


def analyze(rx_text: str, age: float, weight: float | None, sex: str | None) -> dict:
    """Run the same clinical pipeline; return a result blob for the UI."""
    items = parse_prescription(rx_text)
    if not items:
        return {"empty": True}

    patient = Patient(
        age_years=float(age),
        weight_kg=float(weight) if weight not in (None, "") else None,
        sex=sex if sex in {"M", "F"} else None,
    )
    result = resolve_prescription(items)
    resolved = result["resolved"]
    needs = result["needs_confirmation"]
    dose = daily_dose_by_ingredient(resolved, patient)
    alerts = _collect_alerts(dose=dose, patient=patient, resolved=resolved)

    ingredient_names = sorted(
        {
            ing.get("ingredient")
            for item in resolved
            for ing in (item.get("ingredients") or [])
            if ing.get("ingredient")
        }
    )

    return {
        "empty": False,
        "patient": {
            "age_years": patient.age_years,
            "weight_kg": patient.weight_kg,
            "sex": patient.sex,
        },
        "patient_obj_age": patient.age_years,
        "patient_obj_weight": patient.weight_kg,
        "resolved": resolved,
        "needs": needs,
        "dose": dose,
        "alerts": alerts,
        "ingredient_names": ingredient_names,
        "medicines_count": len(resolved) + len(needs),
        "ingredients_count": len(ingredient_names),
        "critical_count": sum(1 for a in alerts if a["tier"] == "critical"),
        "review_count": sum(1 for a in alerts if a["tier"] == "review"),
    }


def render_results(analysis: dict) -> None:
    if analysis.get("empty"):
        st.warning("No medicine lines found. Enter one medicine per line.")
        return

    patient = Patient(
        age_years=float(analysis["patient"]["age_years"]),
        weight_kg=analysis["patient"]["weight_kg"],
        sex=analysis["patient"]["sex"],
    )

    ui.metric_strip(
        analysis["medicines_count"],
        analysis["ingredients_count"],
        analysis["critical_count"],
        analysis["review_count"],
    )
    ui.verdict_card(analysis["critical_count"])

    # ---- Alerts ----
    ui.section_title("Safety alerts")
    critical = [a for a in analysis["alerts"] if a["tier"] == "critical"]
    review = [a for a in analysis["alerts"] if a["tier"] == "review"]
    info = [a for a in analysis["alerts"] if a["tier"] == "info"]

    if critical:
        st.markdown("**Critical**")
        for a in critical:
            ui.alert_card(
                tier="critical",
                icon=a["icon"],
                title=a["title"],
                reason=a["reason"],
                action=a["action"],
                rule=a["rule"],
            )
    if review:
        st.markdown("**Review**")
        for a in review:
            ui.alert_card(
                tier="review",
                icon=a["icon"],
                title=a["title"],
                reason=a["reason"],
                action=a["action"],
                rule=a["rule"],
            )
    if info:
        with st.expander(f"Info alerts ({len(info)})", expanded=False):
            for a in info:
                ui.alert_card(
                    tier="info",
                    icon=a["icon"],
                    title=a["title"],
                    reason=a["reason"],
                    action=a["action"],
                    rule=a["rule"],
                )
    if not critical and not review and not info and not analysis["needs"]:
        st.success("No duplicate-ingredient, dose, or interaction alerts for resolved lines.")

    # ---- Medicines ----
    ui.section_title("Medicines found")
    for item in analysis["resolved"]:
        ui.medicine_card(
            raw_line=item.get("raw", ""),
            brand=item.get("brand_name", ""),
            form=item.get("form_hint"),
            status=item.get("resolve_status", "exact"),
            ingredient_chips=_ingredient_chips(item.get("ingredients") or []),
        )
    for item in analysis["needs"]:
        cands = [c.get("name", "") for c in (item.get("candidates") or [])]
        ui.medicine_card(
            raw_line=item.get("raw", ""),
            brand="Needs confirmation",
            form=item.get("form_hint"),
            status=item.get("resolve_status", "not_found"),
            ingredient_chips=[],
            needs_confirmation=True,
            candidates=cands,
        )

    # ---- Daily dose chart + table ----
    ui.section_title("Daily dose by ingredient")
    by_ing = (analysis.get("dose") or {}).get("by_ingredient") or []
    if by_ing:
        try:
            import plotly.graph_objects as go

            names = [r["ingredient"] for r in by_ing]
            totals = [float(r["total_mg_per_day"]) for r in by_ing]
            limits = [_limit_for_ingredient(r["ingredient"], patient) for r in by_ing]
            colors = []
            for total, lim in zip(totals, limits, strict=False):
                if lim is not None and total > lim:
                    colors.append(ui.CRITICAL)
                else:
                    colors.append(ui.TEAL)

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    y=names,
                    x=totals,
                    orientation="h",
                    marker_color=colors,
                    name="Daily total (mg)",
                    hovertemplate="%{y}: %{x:.0f}<extra></extra>",
                )
            )
            for name, lim in zip(names, limits, strict=False):
                if lim is None:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=[lim],
                        y=[name],
                        mode="markers",
                        marker=dict(
                            symbol="line-ns-open",
                            size=18,
                            color=ui.CRITICAL,
                            line=dict(width=3),
                        ),
                        name="Limit",
                        showlegend=False,
                        hovertemplate=f"Limit: {lim:g}<extra></extra>",
                    )
                )
            fig.update_layout(
                height=max(220, 48 * len(names) + 80),
                margin=dict(l=10, r=20, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="mg / day",
                yaxis=dict(autorange="reversed"),
                font=dict(family="Inter", size=13),
                bargap=0.35,
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            chart_df = pd.DataFrame(
                {
                    "ingredient": [r["ingredient"] for r in by_ing],
                    "mg_per_day": [r["total_mg_per_day"] for r in by_ing],
                }
            ).set_index("ingredient")
            st.bar_chart(chart_df)

        dose_rows = []
        for row in by_ing:
            unit = row["unit"]
            brands = ", ".join(
                f"{c['brand']} ({ui.fmt_qty(c['mg_per_day'], unit)}/day"
                + (" [assumed max]" if c.get("assumed_max") else "")
                + ")"
                for c in row.get("contributions") or []
            )
            lim = _limit_for_ingredient(row["ingredient"], patient)
            dose_rows.append(
                {
                    "Ingredient": row["ingredient"],
                    "Total / day": ui.fmt_qty(row["total_mg_per_day"], unit),
                    "Draft limit": ui.fmt_qty(lim, "mg") if lim is not None else "—",
                    "Contributing brands": brands,
                }
            )
        st.table(pd.DataFrame(dose_rows))
    else:
        st.info("No daily totals computed (nothing resolved, or all strengths unclear).")

    # ---- Stepper ----
    ui.section_title("How this was checked")
    ui.stepper(completed=5)

    with st.expander("Patient used for this check"):
        st.write(analysis["patient"])

    ui.footer()


def main() -> None:
    ui.inject_css()
    warm_caches()
    ui.hero()
    ui.banner()

    if "rx_text" not in st.session_state:
        st.session_state["rx_text"] = EXAMPLES["Hidden paracetamol duplication"]["rx"]
    if "patient_age" not in st.session_state:
        st.session_state["patient_age"] = 35.0
    if "patient_weight" not in st.session_state:
        st.session_state["patient_weight"] = 70.0

    left, right = st.columns([0.95, 1.35], gap="large")

    with left:
        ui.section_title("Prescription input")
        rx_text = st.text_area(
            "One medicine per line",
            key="rx_text",
            height=210,
            label_visibility="collapsed",
            placeholder="Tab Dolo 650 1-0-1 x 5 days",
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("Age (years)", min_value=0.0, max_value=120.0, step=1.0, key="patient_age")
        with c2:
            weight = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                max_value=300.0,
                step=0.5,
                key="patient_weight",
            )
        with c3:
            sex = st.selectbox("Sex", options=["", "M", "F"], index=1)

        analyze_clicked = st.button("Analyze prescription", type="primary", use_container_width=True)

        st.caption("Examples")
        chip_cols = st.columns(2)
        for i, label in enumerate(EXAMPLE_CHIPS):
            with chip_cols[i % 2]:
                if st.button(label, key=f"ex_{i}", use_container_width=True):
                    _load_example(label)
                    st.rerun()

    with right:
        if analyze_clicked:
            try:
                st.session_state["analysis"] = analyze(
                    rx_text,
                    age=age,
                    weight=weight or None,
                    sex=sex or None,
                )
            except Exception as exc:  # noqa: BLE001
                st.error(
                    "Something went wrong while analyzing this prescription. "
                    "Please try again or simplify the input."
                )
                st.caption(f"Technical detail: {type(exc).__name__}: {exc}")

        if "analysis" in st.session_state:
            try:
                render_results(st.session_state["analysis"])
            except Exception as exc:  # noqa: BLE001
                st.error("Could not render results. Please re-run Analyze.")
                st.caption(f"Technical detail: {type(exc).__name__}: {exc}")
        else:
            st.markdown(
                '<div class="rx-card"><h3>Results</h3>'
                "<p style='color:#64748B;margin:0;'>Enter a prescription and click "
                "<b>Analyze prescription</b> to see safety findings.</p></div>",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
