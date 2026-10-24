"""RxNorm (NLM RxNav) public API adapter — free, no API key.

Docs: https://rxnav.nlm.nih.gov/RxNormAPIs.html
Base: https://rxnav.nlm.nih.gov/REST/
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger("rxguard.rxnorm")

RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"
SOURCE_NAME = "RxNorm (NLM RxNav REST API)"
SOURCE_DOCS = "https://rxnav.nlm.nih.gov/RxNormAPIs.html"
TIMEOUT_S = 12.0

# Simple in-process TTL cache (query -> (expires_epoch, payload))
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 600.0


def _cache_get(key: str) -> Any | None:
    hit = _CACHE.get(key)
    if not hit:
        return None
    expires, value = hit
    if time.time() > expires:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time() + _CACHE_TTL, value)


async def _get_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{RXNAV_BASE}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        res = await client.get(url, params=params)
        res.raise_for_status()
        return res.json()


def _get_json_sync(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{RXNAV_BASE}{path}"
    with httpx.Client(timeout=TIMEOUT_S) as client:
        res = client.get(url, params=params)
        res.raise_for_status()
        return res.json()


def check_rxnorm_connectivity() -> dict[str, Any]:
    """Live ping of RxNorm version endpoint."""
    try:
        data = _get_json_sync("/version.json")
        return {
            "ok": True,
            "source": SOURCE_NAME,
            "docs": SOURCE_DOCS,
            "version": data,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.warning("RxNorm connectivity failed: %s", type(exc).__name__)
        return {
            "ok": False,
            "source": SOURCE_NAME,
            "docs": SOURCE_DOCS,
            "error": type(exc).__name__,
            "detail": str(exc)[:200],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def search_rxnorm(query: str, *, max_results: int = 15) -> dict[str, Any]:
    """
    Search RxNorm by string + approximate match.

    Returns exact RXCUI hits and approximate suggestions separately.
    Does not fabricate records when empty.
    """
    q = (query or "").strip()
    if not q:
        return {
            "query": query,
            "exact": [],
            "suggestions": [],
            "items": [],
            "source": SOURCE_NAME,
            "message": "Empty query",
        }

    cache_key = f"search:{q.lower()}:{max_results}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    retrieved_at = datetime.now(timezone.utc).isoformat()
    exact: list[dict[str, Any]] = []
    suggestions: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        # findRxcuiByString — exact/near name match
        data = _get_json_sync("/rxcui.json", {"name": q, "search": 1})
        ids = (data.get("idGroup") or {}).get("rxnormId") or []
        for rxcui in ids[:max_results]:
            props = _concept_properties(str(rxcui))
            if props:
                exact.append(props)
    except httpx.TimeoutException:
        errors.append("RxNorm timeout on findRxcuiByString")
    except httpx.HTTPError as exc:
        errors.append(f"RxNorm HTTP error: {type(exc).__name__}")

    # Approximate matches when few exact hits
    if len(exact) < 3:
        try:
            approx = _get_json_sync(
                "/approximateTerm.json",
                {"term": q, "maxEntries": max_results},
            )
            candidates = (
                (approx.get("approximateGroup") or {}).get("candidate") or []
            )
            seen = {e["source_record_id"] for e in exact}
            for c in candidates:
                rxcui = str(c.get("rxcui") or "")
                if not rxcui or rxcui in seen:
                    continue
                rank = c.get("rank")
                props = _concept_properties(rxcui)
                if not props:
                    # Minimal suggestion from approximate payload only
                    name = c.get("name") or c.get("candidate") or f"RXCUI {rxcui}"
                    props = {
                        "name": name,
                        "source_record_id": rxcui,
                        "tty": c.get("tty"),
                        "match_type": "suggestion",
                        "similarity": None,
                        "ingredients": [],
                        "strength_label": None,
                        "dosage_form": None,
                        "source": SOURCE_NAME,
                        "source_url": f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}",
                        "verification_status": "SOURCE_BACKED",
                        "geographic_applicability": "US_RXNORM",
                        "is_synthetic": False,
                        "note": "Approximate RxNorm match — confirm before use. Not an Indian brand catalogue.",
                    }
                else:
                    props["match_type"] = "suggestion"
                    props["similarity"] = float(rank) if rank is not None else None
                suggestions.append(props)
                seen.add(rxcui)
                if len(suggestions) >= max_results:
                    break
        except httpx.TimeoutException:
            errors.append("RxNorm timeout on approximateTerm")
        except httpx.HTTPError as exc:
            errors.append(f"RxNorm approximate HTTP error: {type(exc).__name__}")

    for e in exact:
        e["match_type"] = "exact"
        e["similarity"] = 100.0

    message = None
    if not exact and not suggestions:
        message = "No suitable match was found in the available sources."

    result = {
        "query": q,
        "exact": exact,
        "suggestions": suggestions,
        "items": exact + suggestions,
        "source": SOURCE_NAME,
        "source_docs": SOURCE_DOCS,
        "retrieved_at": retrieved_at,
        "errors": errors,
        "message": message,
        "limitation": (
            "RxNorm is a US NLM terminology. It does not provide a complete "
            "Indian retail brand catalogue. Brand names like Dolo/Crocin may "
            "not resolve to Indian SKUs."
        ),
    }
    if not errors:
        _cache_set(cache_key, result)
    return result


def _concept_properties(rxcui: str) -> dict[str, Any] | None:
    cache_key = f"rxcui:{rxcui}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        props_data = _get_json_sync(f"/rxcui/{quote(rxcui)}/properties.json")
        props = (props_data.get("properties") or {})
        name = props.get("name")
        if not name:
            return None
        tty = props.get("tty")

        ingredients: list[dict[str, Any]] = []
        strength_label = None
        dosage_form = None

        try:
            related = _get_json_sync(
                f"/rxcui/{quote(rxcui)}/related.json",
                {"tty": "IN+PIN+MIN+DF+SCD+SBD"},
            )
            groups = (related.get("relatedGroup") or {}).get("conceptGroup") or []
            for g in groups:
                g_tty = g.get("tty")
                for c in g.get("conceptProperties") or []:
                    if g_tty in {"IN", "PIN", "MIN"}:
                        ingredients.append(
                            {
                                "canonical_name": c.get("name"),
                                "rxcui": c.get("rxcui"),
                                "tty": g_tty,
                            }
                        )
                    elif g_tty == "DF" and not dosage_form:
                        dosage_form = c.get("name")
        except httpx.HTTPError:
            pass

        # Strength often encoded in SCD/SBD name; keep null if not separately available
        out = {
            "name": name,
            "source_record_id": str(rxcui),
            "tty": tty,
            "ingredients": ingredients,
            "strength_label": strength_label,
            "dosage_form": dosage_form,
            "source": SOURCE_NAME,
            "source_url": f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json",
            "verification_status": "SOURCE_BACKED"
            if ingredients
            else "PARTIALLY_VERIFIED",
            "geographic_applicability": "US_RXNORM",
            "is_synthetic": False,
            "note": (
                "Retrieved from RxNorm. Public terminology record — not "
                "clinically validated for Indian prescribing workflows."
            ),
        }
        _cache_set(cache_key, out)
        return out
    except httpx.HTTPError:
        return None
