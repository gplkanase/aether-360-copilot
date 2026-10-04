"""Cited Q&A over Member 360 + document chunks. Never answers without sources."""
from __future__ import annotations

import re
from typing import Any

from aether360.guardrails import check_question
from aether360.retrieve import search_chunks
from aether360.store import Bundle

MEMBER_RE = re.compile(r"\bMEM-\d+\b", re.I)
NAME_HINTS = {
    "jordan hale": "MEM-10007",
    "jordan": "MEM-10007",
    "hale": "MEM-10007",
    "river chen": "MEM-10014",
    "river": "MEM-10014",
    "chen": "MEM-10014",
    "avery okonkwo": "MEM-10021",
    "okonkwo": "MEM-10021",
    "samira patel": "MEM-10003",
    "samira": "MEM-10003",
    "ellis navarro": "MEM-10031",
    "navarro": "MEM-10031",
    "morgan blake": "MEM-10018",
    "blake": "MEM-10018",
}

REG_CLASSES = {"fda_label", "cms_ncd", "safety_alert", "pa_policy", "formulary", "quality_spec"}
CLINICAL_CLASSES = {"clinical_note"}


def resolve_member(question: str, bundle: Bundle, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit.upper()
    m = MEMBER_RE.search(question or "")
    if m:
        return m.group(0).upper()
    q = (question or "").lower()
    for hint, mid in NAME_HINTS.items():
        if hint in q:
            return mid
    return None


def _source(claim: str, object_name: str, key: str, snippet: str, source_type: str = "structured") -> dict[str, str]:
    return {
        "claim": claim,
        "source_type": source_type,
        "object": object_name,
        "key": key,
        "snippet": (snippet or "")[:500],
    }


def _factors_for(bundle: Bundle, member_id: str) -> list[dict[str, Any]]:
    return [f for f in bundle.atri_factors if f["member_id"] == member_id]


def _population_answer(question: str, bundle: Bundle) -> dict[str, Any]:
    rows = bundle.member_360
    n = len(rows)
    very_high = [r for r in rows if r["atri_tier"] == "Very High"]
    high = [r for r in rows if r["atri_tier"] == "High"]
    readmit = [r for r in rows if r["readmit_30d_flag"]]
    gaps = bundle.care_gaps
    q = question.lower()
    sources = [
        _source(
            f"{n} synthetic members in GOLD.MEMBER_360 as of {bundle.as_of}",
            "GOLD.MEMBER_360",
            f"n={n}",
            f"as_of={bundle.as_of}; members={n}",
        )
    ]
    if "very high" in q or "highest risk" in q or "high risk" in q:
        names = ", ".join(f"{r['full_name']} ({r['member_id']}, ATRI {r['atri_score']})" for r in very_high[:8])
        if high and "very" not in q:
            names = ", ".join(
                f"{r['full_name']} ({r['member_id']}, {r['atri_tier']} {r['atri_score']})"
                for r in (very_high + high)[:10]
            )
            text = f"High or Very High ATRI: {names}."
        else:
            text = f"Very High ATRI members: {names or 'none'}."
        for r in (very_high + high)[:5]:
            sources.append(
                _source(
                    f"{r['full_name']} ATRI {r['atri_score']} {r['atri_tier']}",
                    "GOLD.MEMBER_360",
                    r["member_id"],
                    f"tier={r['atri_tier']} score={r['atri_score']} factors_see=GOLD.ATRI_FACTORS",
                )
            )
        return {"answer": text, "sources": sources, "response_type": "cited", "member_id": None}
    if "readmit" in q:
        names = ", ".join(f"{r['full_name']} ({r['member_id']})" for r in readmit)
        sources.append(
            _source(
                "Unplanned 30-day readmission flag",
                "GOLD.MEMBER_360",
                "readmit_30d_flag",
                names or "none",
            )
        )
        return {
            "answer": f"Members with unplanned 30-day readmission: {names or 'none in this synthetic panel'}.",
            "sources": sources,
            "response_type": "cited",
            "member_id": None,
        }
    if "gap" in q or "a1c" in q or "hedis" in q or "gsd" in q:
        a1c_gaps = [g for g in gaps if g["measure"] == "GSD-A1c"]
        listing = ", ".join(sorted({g["member_id"] for g in a1c_gaps}))
        sources.append(
            _source("Open glycemic assessment gaps", "GOLD.CARE_GAPS", "GSD-A1c", listing or "none")
        )
        return {
            "answer": f"Open GSD-style A1c gaps: {listing or 'none'}. Gap rule: last A1c older than 180 days for members with diabetes.",
            "sources": sources,
            "response_type": "cited",
            "member_id": None,
        }
    if "how many" in q or "count" in q or "panel" in q:
        by_tier = {}
        for r in rows:
            by_tier[r["atri_tier"]] = by_tier.get(r["atri_tier"], 0) + 1
        text = "; ".join(f"{k}: {v}" for k, v in sorted(by_tier.items()))
        sources.append(_source("ATRI tier mix", "GOLD.MEMBER_360", "atri_tier", text))
        return {
            "answer": f"Synthetic panel size {n}. ATRI mix: {text}.",
            "sources": sources,
            "response_type": "cited",
            "member_id": None,
        }
    return {
        "answer": f"Synthetic panel: {n} members as of {bundle.as_of}. Name a member (e.g. MEM-10007 Jordan Hale) or ask about Very High ATRI, readmissions, or A1c gaps.",
        "sources": sources,
        "response_type": "cited",
        "member_id": None,
    }


def _member_answer(question: str, bundle: Bundle, member_id: str) -> dict[str, Any]:
    row = bundle.member(member_id)
    if not row:
        return {
            "answer": f"{member_id} is not in the synthetic MEMBER_360 table.",
            "sources": [],
            "response_type": "abstain",
            "member_id": member_id,
        }
    factors = _factors_for(bundle, member_id)
    q = question.lower()
    sources = [
        _source(
            f"{row['full_name']} ATRI {row['atri_score']} ({row['atri_tier']})",
            "GOLD.MEMBER_360",
            member_id,
            f"age={row['age_years']} panel={row['panel']} LOB={row['line_of_business']} meds={row['active_med_count']}",
        )
    ]
    for f in factors:
        sources.append(
            _source(
                f"{f['factor_code']} +{f['points']}",
                f"GOLD.ATRI_FACTORS/{f['source_object']}",
                f["source_key"],
                f["evidence"],
            )
        )

    if any(k in q for k in ("why", "risk", "atri", "factor", "strat")):
        lines = [
            f"**{row['full_name']}** (`{member_id}` / `{row['patient_id']}`) ATRI **{row['atri_score']} {row['atri_tier']}** (as of {row['as_of']}). This is a transparent rules index, not a mortality prediction.",
            "",
            "Contributing factors:",
        ]
        for f in sorted(factors, key=lambda x: -x["points"]):
            lines.append(f"- `{f['factor_code']}` **+{f['points']}** — {f['evidence']} ({f['source_object']} · {f['source_key']})")
        if row["safety_flag_list"]:
            lines.append(f"\nSafety flags: {row['safety_flag_list']}")
        return {"answer": "\n".join(lines), "sources": sources, "response_type": "cited", "member_id": member_id}

    if any(k in q for k in ("med", "drug", "warfarin", "ibuprofen", "sglt", "statin", "glp")):
        lines = [
            f"Active medications for **{row['full_name']}**: {row['active_med_list'] or 'none on file'}.",
        ]
        sources.append(
            _source("Active medication list", "GOLD.MEMBER_360.active_med_list", member_id, row["active_med_list"])
        )
        return {"answer": "\n".join(lines), "sources": sources, "response_type": "cited", "member_id": member_id}

    profile = [
        f"**{row['full_name']}** `{member_id}` (EHR `{row['patient_id']}`), age {row['age_years']}, {row['sex']}, {row['region']}.",
        f"Coverage: {row['line_of_business']} / {row['product_name']}. Panel: {row['panel']}. PCP: {row['pcp_name']}.",
        f"ATRI {row['atri_score']} {row['atri_tier']}. Conditions: {row['active_condition_list']}.",
        f"Meds ({row['active_med_count']}): {row['active_med_list']}.",
        f"ED visits 90d: {row['ed_visits_90d']}. 30-day readmit: {row['readmit_30d_flag']}. Last encounter: {row['last_encounter_date']}.",
        f"Last A1c: {row['last_a1c_value']} on {row['last_a1c_date']}. Open gaps: {row['open_gap_list'] or 'none'}.",
        f"Safety: {row['safety_flag_list'] or 'none'}. Allowed medical 12m: ${row['allowed_12m']:,.0f}.",
    ]
    return {"answer": "\n".join(profile), "sources": sources, "response_type": "cited", "member_id": member_id}


def _doc_answer(question: str, bundle: Bundle, member_id: str | None) -> dict[str, Any]:
    q = question.lower()
    classes = None
    if any(k in q for k in ("ncd", "cms", "cgm", "coverage", "pa ", "prior auth", "formulary", "glp")):
        classes = ["cms_ncd", "pa_policy", "formulary"]
    elif any(k in q for k in ("label", "fda", "boxed", "nsaid", "warfarin", "metformin", "eGFR", "egfr")):
        classes = ["fda_label", "safety_alert"]
    elif any(k in q for k in ("sglt", "dka", "ketone", "safety alert")):
        classes = ["safety_alert", "fda_label", "clinical_note"]
    elif any(k in q for k in ("note", "discharge", "ed ", "pharmacist")):
        classes = ["clinical_note"]

    hits = search_chunks(question, bundle.chunks, member_id=member_id, document_classes=classes, limit=5)
    if not hits:
        hits = search_chunks(question, bundle.chunks, member_id=member_id, limit=5)
    rare = [t for t in re.findall(r"[a-z0-9\-]{10,}", question.lower())]
    if hits and rare:
        joined = " ".join(h.get("text", "").lower() for h in hits)
        if not any(t in joined for t in rare):
            hits = []
    if not hits:
        return {
            "answer": "No supporting document chunks were retrieved. Abstaining rather than guessing.",
            "sources": [],
            "response_type": "abstain",
            "member_id": member_id,
        }
    lines = [
        "Retrieved evidence (quoted, not inferred beyond the snippet):",
        "",
    ]
    sources = []
    for i, h in enumerate(hits, start=1):
        quote = h["text"].strip().replace("\n", " ")
        if len(quote) > 420:
            quote = quote[:420] + "…"
        who = f" · {h['member_id']}" if h.get("member_id") else ""
        lines.append(f"**[{i}] {h['title']}** (`{h['chunk_id']}`{who})")
        lines.append(f"> {quote}")
        lines.append("")
        sources.append(
            _source(
                h["title"],
                h["doc_id"],
                h["chunk_id"],
                h["text"],
                source_type="document",
            )
        )
    lines.append("If you need a member-specific overlay, include a member id so structured rows can be joined.")
    return {"answer": "\n".join(lines), "sources": sources, "response_type": "cited", "member_id": member_id}


def _mixed_safety(question: str, bundle: Bundle, member_id: str) -> dict[str, Any]:
    member_part = _member_answer(question, bundle, member_id)
    doc_part = _doc_answer(question, bundle, member_id)
    if member_part["response_type"] == "abstain":
        return member_part
    sources = member_part["sources"] + doc_part["sources"]
    if not doc_part["sources"]:
        return {
            "answer": member_part["answer"]
            + "\n\nNo additional document chunks matched. Not inferring a label-level conclusion.",
            "sources": member_part["sources"],
            "response_type": "cited",
            "member_id": member_id,
        }
    answer = (
        member_part["answer"]
        + "\n\n---\n**Document evidence**\n\n"
        + doc_part["answer"]
    )
    return {"answer": answer, "sources": sources, "response_type": "cited", "member_id": member_id}


def answer_question(
    question: str,
    bundle: Bundle,
    *,
    member_id: str | None = None,
) -> dict[str, Any]:
    gate = check_question(question)
    if not gate["ok"]:
        return {
            "answer": gate["reason"],
            "sources": [],
            "response_type": gate["action"],
            "member_id": None,
        }

    mid = resolve_member(question, bundle, member_id)
    q = question.lower()
    wants_docs = any(
        k in q
        for k in (
            "label",
            "ncd",
            "cms",
            "policy",
            "alert",
            "note",
            "ibuprofen",
            "nsaid",
            "warfarin",
            "sglt",
            "dka",
            "cgm",
            "glp",
            "semaglutide",
            "coverage",
            "formulary",
            "metforax",
            "egfr",
            "boxed",
            "warning",
            "contraindic",
            "dosing",
            "corpus",
        )
    )
    wants_risk = any(k in q for k in ("why", "risk", "atri", "factor", "360", "profile", "gap"))
    population = mid is None and any(
        k in q for k in ("how many", "which members", "list", "panel", "highest", "very high", "readmit")
    )

    if mid and wants_docs:
        result = _mixed_safety(question, bundle, mid)
    elif mid:
        result = _member_answer(question, bundle, mid)
        if wants_docs:
            result = _mixed_safety(question, bundle, mid)
    elif wants_docs and not population:
        result = _doc_answer(question, bundle, None)
    elif population or mid is None:
        result = _population_answer(question, bundle)
        if wants_docs:
            doc = _doc_answer(question, bundle, None)
            if doc["sources"]:
                result = {
                    "answer": result["answer"] + "\n\n---\n" + doc["answer"],
                    "sources": result["sources"] + doc["sources"],
                    "response_type": "cited",
                    "member_id": None,
                }
    else:
        result = _population_answer(question, bundle)

    if result["response_type"] == "cited" and not result["sources"]:
        result["response_type"] = "abstain"
        result["answer"] = "Insufficient evidence in the synthetic corpus. Abstaining."
    result["question"] = question
    result["confidence"] = "high" if len(result["sources"]) >= 2 else ("medium" if result["sources"] else "none")
    if wants_risk:
        pass
    return result
