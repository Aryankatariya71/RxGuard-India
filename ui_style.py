"""Presentation helpers and CSS for RxGuard India (no clinical logic)."""

from __future__ import annotations

from typing import Any

import streamlit as st

PRIMARY = "#0B3C5D"
TEAL = "#1A7A7A"
ACCENT = "#148F77"
CRITICAL = "#C0392B"
REVIEW = "#D68910"
INFO = "#2471A3"
OK = "#1E8449"
SOFT_BG = "#F4F7FA"
CARD_BG = "#FFFFFF"


def inject_css() -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"]  {{
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}}

/* Hide Streamlit chrome */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
[data-testid="stToolbar"] {{display: none;}}
.block-container {{
  padding-top: 1.2rem;
  padding-bottom: 2.5rem;
  max-width: 1280px;
}}

.rx-hero {{
  background: linear-gradient(135deg, {PRIMARY} 0%, {TEAL} 100%);
  color: white;
  border-radius: 18px;
  padding: 1.4rem 1.6rem 1.2rem 1.6rem;
  margin-bottom: 0.9rem;
  box-shadow: 0 10px 30px rgba(11, 60, 93, 0.18);
}}
.rx-hero h1 {{
  margin: 0;
  font-size: 1.85rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}}
.rx-hero .subtitle {{
  margin: 0.25rem 0 0.85rem 0;
  opacity: 0.92;
  font-size: 0.98rem;
  font-weight: 400;
}}
.rx-chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}}
.rx-chip {{
  background: rgba(255,255,255,0.14);
  border: 1px solid rgba(255,255,255,0.22);
  border-radius: 999px;
  padding: 0.28rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 500;
}}

.rx-banner {{
  background: #FFF8E7;
  border: 1px solid #F0D9A0;
  color: #7A5B12;
  border-radius: 12px;
  padding: 0.55rem 0.9rem;
  font-size: 0.86rem;
  margin-bottom: 1rem;
  font-weight: 500;
}}

.rx-card {{
  background: {CARD_BG};
  border: 1px solid #E6ECF1;
  border-radius: 16px;
  padding: 1.05rem 1.15rem;
  box-shadow: 0 6px 18px rgba(15, 40, 60, 0.05);
  margin-bottom: 0.9rem;
}}
.rx-card h3 {{
  margin: 0 0 0.7rem 0;
  font-size: 1.02rem;
  color: {PRIMARY};
  font-weight: 650;
}}

.rx-metric-row {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.7rem;
  margin-bottom: 0.9rem;
}}
@media (max-width: 900px) {{
  .rx-metric-row {{ grid-template-columns: repeat(2, 1fr); }}
}}
.rx-metric {{
  background: {CARD_BG};
  border: 1px solid #E6ECF1;
  border-radius: 14px;
  padding: 0.85rem 0.95rem;
  box-shadow: 0 4px 14px rgba(15, 40, 60, 0.04);
}}
.rx-metric .label {{
  font-size: 0.75rem;
  color: #627384;
  font-weight: 500;
  margin-bottom: 0.2rem;
}}
.rx-metric .value {{
  font-size: 1.45rem;
  font-weight: 700;
  color: {PRIMARY};
  line-height: 1.1;
}}
.rx-metric.critical .value {{ color: {CRITICAL}; }}
.rx-metric.review .value {{ color: {REVIEW}; }}

.rx-verdict {{
  border-radius: 14px;
  padding: 0.9rem 1.05rem;
  font-weight: 650;
  margin-bottom: 0.9rem;
  border: 1px solid transparent;
}}
.rx-verdict.bad {{
  background: #FDEDEC;
  border-color: #F5B7B1;
  color: {CRITICAL};
}}
.rx-verdict.good {{
  background: #E8F8F5;
  border-color: #A9DFBF;
  color: {OK};
}}

.rx-alert {{
  border-radius: 12px;
  padding: 0.85rem 0.95rem;
  margin-bottom: 0.65rem;
  background: {CARD_BG};
  border: 1px solid #E6ECF1;
  border-left: 5px solid #95A5A6;
  box-shadow: 0 3px 10px rgba(15, 40, 60, 0.04);
}}
.rx-alert.critical {{ border-left-color: {CRITICAL}; background: #FFF7F6; }}
.rx-alert.review {{ border-left-color: {REVIEW}; background: #FFFBF2; }}
.rx-alert.info {{ border-left-color: {INFO}; background: #F4F9FC; }}
.rx-alert .title {{
  font-weight: 700;
  color: {PRIMARY};
  margin-bottom: 0.2rem;
  font-size: 0.95rem;
}}
.rx-alert .reason {{
  color: #334155;
  font-size: 0.9rem;
  margin-bottom: 0.35rem;
  line-height: 1.4;
  white-space: normal;
  word-break: break-word;
}}
.rx-alert .action {{
  color: #475569;
  font-size: 0.84rem;
  margin-bottom: 0.35rem;
}}
.rx-alert .rule {{
  display: inline-block;
  background: #EEF2F6;
  color: #64748B;
  border-radius: 999px;
  padding: 0.15rem 0.55rem;
  font-size: 0.72rem;
  font-weight: 500;
}}

.rx-med {{
  border: 1px solid #E6ECF1;
  border-radius: 14px;
  padding: 0.85rem 0.95rem;
  margin-bottom: 0.65rem;
  background: {CARD_BG};
}}
.rx-med .line {{
  font-size: 0.78rem;
  color: #64748B;
  margin-bottom: 0.2rem;
  word-break: break-word;
}}
.rx-med .brand {{
  font-size: 1.02rem;
  font-weight: 650;
  color: {PRIMARY};
  margin-bottom: 0.35rem;
  word-break: break-word;
}}
.rx-badge {{
  display: inline-block;
  border-radius: 999px;
  padding: 0.12rem 0.55rem;
  font-size: 0.72rem;
  font-weight: 650;
  margin-right: 0.35rem;
  margin-bottom: 0.35rem;
}}
.rx-badge.exact {{ background: #D5F5E3; color: {OK}; }}
.rx-badge.confident {{ background: #D6EAF8; color: {TEAL}; }}
.rx-badge.ambiguous {{ background: #FCF3CF; color: {REVIEW}; }}
.rx-badge.not_found {{ background: #FADBD8; color: {CRITICAL}; }}
.rx-ing {{
  display: inline-block;
  background: #EEF5F8;
  color: #1F4E5F;
  border-radius: 999px;
  padding: 0.18rem 0.6rem;
  font-size: 0.78rem;
  margin: 0.15rem 0.25rem 0.15rem 0;
  white-space: normal;
  word-break: break-word;
}}

.rx-stepper {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  margin-top: 0.35rem;
}}
.rx-step {{
  background: #EEF2F6;
  color: #64748B;
  border-radius: 999px;
  padding: 0.28rem 0.7rem;
  font-size: 0.76rem;
  font-weight: 500;
}}
.rx-step.done {{
  background: #D5F5E3;
  color: {OK};
  font-weight: 650;
}}
.rx-step-arrow {{
  color: #94A3B8;
  font-size: 0.8rem;
}}

.rx-footer {{
  margin-top: 1.2rem;
  padding-top: 0.8rem;
  border-top: 1px solid #E6ECF1;
  color: #64748B;
  font-size: 0.78rem;
  line-height: 1.45;
}}

div[data-testid="stButton"] > button[kind="primary"] {{
  background: {PRIMARY};
  border-color: {PRIMARY};
  border-radius: 12px;
  font-weight: 650;
  padding: 0.55rem 1rem;
}}
div[data-testid="stButton"] > button {{
  border-radius: 999px;
  font-weight: 550;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        """
<div class="rx-hero">
  <h1>RxGuard India</h1>
  <div class="subtitle">Prescription Safety Checker for Indian Brand Medicines</div>
  <div class="rx-chips">
    <span class="rx-chip">2.5 lakh brands</span>
    <span class="rx-chip">Explainable rules engine</span>
    <span class="rx-chip">Works offline</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def banner() -> None:
    st.markdown(
        '<div class="rx-banner">Decision support only. Prototype, not clinically verified.</div>',
        unsafe_allow_html=True,
    )


def metric_strip(medicines: int, ingredients: int, critical: int, review: int) -> None:
    st.markdown(
        f"""
<div class="rx-metric-row">
  <div class="rx-metric"><div class="label">Medicines found</div><div class="value">{medicines}</div></div>
  <div class="rx-metric"><div class="label">Ingredients</div><div class="value">{ingredients}</div></div>
  <div class="rx-metric critical"><div class="label">Critical alerts</div><div class="value">{critical}</div></div>
  <div class="rx-metric review"><div class="label">Review alerts</div><div class="value">{review}</div></div>
</div>
        """,
        unsafe_allow_html=True,
    )


def verdict_card(critical_count: int) -> None:
    if critical_count > 0:
        st.markdown(
            f'<div class="rx-verdict bad">ACTION NEEDED: {critical_count} critical issue'
            f'{"s" if critical_count != 1 else ""}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="rx-verdict good">No critical issues found</div>',
            unsafe_allow_html=True,
        )


def alert_card(
    *,
    tier: str,
    icon: str,
    title: str,
    reason: str,
    action: str,
    rule: str,
) -> None:
    css = tier if tier in {"critical", "review", "info"} else "info"
    st.markdown(
        f"""
<div class="rx-alert {css}">
  <div class="title">{icon} {title}</div>
  <div class="reason">{reason}</div>
  <div class="action"><b>Suggested action:</b> {action}</div>
  <span class="rule">Rule: {rule}</span>
</div>
        """,
        unsafe_allow_html=True,
    )


def medicine_card(
    *,
    raw_line: str,
    brand: str,
    form: str | None,
    status: str,
    ingredient_chips: list[str],
    needs_confirmation: bool = False,
    candidates: list[str] | None = None,
) -> None:
    status_key = (status or "not_found").replace(" ", "_")
    if status_key not in {"exact", "confident", "ambiguous", "not_found"}:
        status_key = "not_found"
    form_txt = f" · {form}" if form else ""
    chips = "".join(f'<span class="rx-ing">{c}</span>' for c in ingredient_chips) or (
        '<span class="rx-ing">No ingredients</span>'
    )
    extra = ""
    if needs_confirmation:
        cand = ", ".join(candidates or []) or "No candidates"
        extra = (
            f'<div class="reason" style="margin-top:0.4rem;color:#7B241C;">'
            f"<b>Needs confirmation.</b> Candidates: {cand}</div>"
        )
    st.markdown(
        f"""
<div class="rx-med">
  <div class="line">{raw_line}</div>
  <div class="brand">{brand}{form_txt}</div>
  <span class="rx-badge {status_key}">{status}</span>
  <div style="margin-top:0.35rem;">{chips}</div>
  {extra}
</div>
        """,
        unsafe_allow_html=True,
    )


def stepper(completed: int = 5) -> None:
    steps = [
        "Parse",
        "Match brands",
        "Split ingredients",
        "Sum daily dose",
        "Check duplicates, interactions, doses",
    ]
    parts: list[str] = ['<div class="rx-stepper">']
    for i, label in enumerate(steps):
        cls = "rx-step done" if i < completed else "rx-step"
        parts.append(f'<span class="{cls}">{label}</span>')
        if i < len(steps) - 1:
            parts.append('<span class="rx-step-arrow">→</span>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        """
<div class="rx-footer">
  Data: A-Z Medicines Dataset of India, DDInter (academic use).
  Dose rules are DRAFT pending pharmacist verification.
</div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str) -> None:
    """Section header that visually matches cards (widgets cannot nest inside HTML)."""
    st.markdown(
        f'<div class="rx-card" style="padding:0.7rem 1rem;margin-bottom:0.55rem;">'
        f"<h3 style='margin:0;'>{title}</h3></div>",
        unsafe_allow_html=True,
    )


def fmt_num(value: Any) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(num - round(num)) < 1e-9:
        return str(int(round(num)))
    return str(num).rstrip("0").rstrip(".")


def fmt_qty(value: Any, unit: str | None) -> str:
    u = (unit or "").strip()
    if not u:
        return fmt_num(value)
    return f"{fmt_num(value)} {u}"
