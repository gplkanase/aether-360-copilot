"""Aether Transparent Risk Index (ATRI) — rule-based, fully cited.

Python is the unit-tested source of truth. SQL in sql/04_gold.sql must match.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

AS_OF = date(2026, 8, 31)

TIER_LOW = (0, 19)
TIER_MOD = (20, 39)
TIER_HIGH = (40, 59)
# 60+ very high

CONDITION_POINTS = {
    "HCC_CHF": (18, ("I50",)),
    "HCC_CKD3P": (12, ("N18.3", "N18.4", "N18.5", "N18.6")),
    "HCC_T2DM": (6, ("E11",)),
    "HCC_COPD": (10, ("J44",)),
    "HCC_AFIB": (8, ("I48",)),
    "HCC_CAD": (8, ("I25",)),
    "HCC_DEP": (5, ("F32", "F33")),
}

WARFARIN_NAMES = {"warfarin", "jantoven"}
NSAID_NAMES = {"ibuprofen", "naproxen", "diclofenac", "meloxicam", "indomethacin"}
STATIN_NAMES = {
    "atorvastatin",
    "rosuvastatin",
    "simvastatin",
    "pravastatin",
    "lovastatin",
    "pitavastatin",
}
SGLT2_NAMES = {"empagliflozin", "dapagliflozin", "canagliflozin"}


@dataclass
class Factor:
    factor_code: str
    points: int
    source_object: str
    source_key: str
    evidence: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "factor_code": self.factor_code,
            "points": self.points,
            "source_object": self.source_object,
            "source_key": self.source_key,
            "evidence": self.evidence,
        }


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    return datetime.strptime(text, "%Y-%m-%d").date()


def age_years(dob: Any, as_of: date = AS_OF) -> int:
    born = parse_date(dob)
    if not born:
        return 0
    years = as_of.year - born.year - ((as_of.month, as_of.day) < (born.month, born.day))
    return years


def icd_matches(code: str, prefixes: Iterable[str]) -> bool:
    c = (code or "").upper().replace(" ", "")
    return any(c.startswith(p.upper()) for p in prefixes)


def med_norm(name: str) -> str:
    return (name or "").strip().lower()


def tier_for(score: int) -> str:
    if score <= TIER_LOW[1]:
        return "Low"
    if score <= TIER_MOD[1]:
        return "Moderate"
    if score <= TIER_HIGH[1]:
        return "High"
    return "Very High"


def _age_factor(member_id: str, dob: Any) -> Factor | None:
    years = age_years(dob)
    key = f"{member_id} / dob"
    if years >= 85:
        return Factor("AGE_85P", 20, "PAYER_MEMBERS", key, f"Age {years} (≥85)")
    if years >= 75:
        return Factor("AGE_75_84", 14, "PAYER_MEMBERS", key, f"Age {years} (75–84)")
    if years >= 65:
        return Factor("AGE_65_74", 8, "PAYER_MEMBERS", key, f"Age {years} (65–74)")
    if years >= 50:
        return Factor("AGE_50_64", 4, "PAYER_MEMBERS", key, f"Age {years} (50–64)")
    return None


def score_member(
    member: dict[str, Any],
    conditions: list[dict[str, Any]],
    medications: list[dict[str, Any]],
    encounters: list[dict[str, Any]],
    labs: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    as_of: date = AS_OF,
) -> dict[str, Any]:
    member_id = member["member_id"]
    factors: list[Factor] = []

    age_f = _age_factor(member_id, member.get("dob"))
    if age_f:
        factors.append(age_f)
    years = age_years(member.get("dob"), as_of)

    fired_hcc: set[str] = set()
    for row in conditions:
        if str(row.get("status", "active")).lower() != "active":
            continue
        icd = str(row.get("icd10", ""))
        for code, (points, prefixes) in CONDITION_POINTS.items():
            if code in fired_hcc:
                continue
            if icd_matches(icd, prefixes):
                fired_hcc.add(code)
                factors.append(
                    Factor(
                        code,
                        points,
                        "EHR_CONDITIONS",
                        f"{member_id} / {icd}",
                        f"{row.get('description') or icd} (active)",
                    )
                )

    active_meds = [
        m
        for m in medications
        if str(m.get("status", "active")).lower() == "active"
    ]
    n_meds = len(active_meds)
    if n_meds >= 8:
        factors.append(
            Factor(
                "POLY_8P",
                12,
                "EHR_MEDICATIONS",
                f"{member_id} / count={n_meds}",
                f"{n_meds} active medications (polypharmacy ≥8)",
            )
        )
    elif n_meds >= 5:
        factors.append(
            Factor(
                "POLY_5_7",
                6,
                "EHR_MEDICATIONS",
                f"{member_id} / count={n_meds}",
                f"{n_meds} active medications (polypharmacy 5–7)",
            )
        )

    ed_90 = [
        e
        for e in encounters
        if str(e.get("encounter_class", "")).lower() == "emergency"
        and parse_date(e.get("start_date"))
        and (as_of - parse_date(e.get("start_date"))).days <= 90
    ]
    if ed_90:
        pts = min(24, 8 * len(ed_90))
        ids = ",".join(e["encounter_id"] for e in ed_90[:4])
        factors.append(
            Factor(
                "ED_90D",
                pts,
                "EHR_ENCOUNTERS",
                ids,
                f"{len(ed_90)} ED visit(s) in last 90 days (8 pts each, cap 24)",
            )
        )

    if any(str(e.get("unplanned_readmit_30d", "")).lower() in {"true", "1", "yes"} for e in encounters):
        hit = next(
            e
            for e in encounters
            if str(e.get("unplanned_readmit_30d", "")).lower() in {"true", "1", "yes"}
        )
        factors.append(
            Factor(
                "READMIT_30D",
                20,
                "EHR_ENCOUNTERS",
                hit["encounter_id"],
                f"Unplanned 30-day readmission on {hit.get('start_date')}",
            )
        )

    has_dm = any(
        icd_matches(str(c.get("icd10", "")), ("E11",))
        and str(c.get("status", "active")).lower() == "active"
        for c in conditions
    )
    a1c_rows = [lb for lb in labs if str(lb.get("loinc") or lb.get("test_code", "")).upper() in {"4548-4", "A1C"}]
    a1c_rows_sorted = sorted(a1c_rows, key=lambda r: parse_date(r.get("result_date")) or date(1900, 1, 1), reverse=True)
    last_a1c = a1c_rows_sorted[0] if a1c_rows_sorted else None
    if has_dm:
        if last_a1c is None:
            factors.append(
                Factor("GAP_A1C", 8, "EHR_LABS", f"{member_id} / missing", "Diabetes without any A1c on file")
            )
        else:
            last_dt = parse_date(last_a1c.get("result_date"))
            if last_dt and (as_of - last_dt).days > 180:
                factors.append(
                    Factor(
                        "GAP_A1C",
                        8,
                        "EHR_LABS",
                        last_a1c.get("lab_id", member_id),
                        f"Last A1c {last_a1c.get('value')} on {last_dt} (>6 months)",
                    )
                )

    pcp_visits = [
        e
        for e in encounters
        if str(e.get("encounter_class", "")).lower() in {"ambulatory", "outpatient", "pcp"}
        and parse_date(e.get("start_date"))
        and (as_of - parse_date(e.get("start_date"))).days <= 365
    ]
    if not pcp_visits:
        factors.append(
            Factor(
                "GAP_PCP",
                6,
                "EHR_ENCOUNTERS",
                f"{member_id} / no PCP 12m",
                "No ambulatory/PCP encounter in last 12 months",
            )
        )

    has_cad = "HCC_CAD" in fired_hcc
    on_statin = any(med_norm(m.get("drug_name", "")).split()[0] in STATIN_NAMES for m in active_meds)
    if has_cad and not on_statin:
        factors.append(
            Factor(
                "GAP_STATIN_CAD",
                7,
                "EHR_MEDICATIONS",
                f"{member_id} / CAD no statin",
                "CAD on problem list without an active statin",
            )
        )

    allowed = sum(float(c.get("allowed_amount") or 0) for c in claims)
    if allowed >= 50000:
        factors.append(
            Factor(
                "HIGH_COST",
                10,
                "PAYER_MEDICAL_CLAIMS",
                f"{member_id} / allowed_12m={allowed:.0f}",
                f"Allowed medical amount last 12m ${allowed:,.0f} (≥$50,000)",
            )
        )

    on_warfarin = [m for m in active_meds if med_norm(m.get("drug_name", "")).split()[0] in WARFARIN_NAMES]
    on_nsaid = [m for m in active_meds if med_norm(m.get("drug_name", "")).split()[0] in NSAID_NAMES]
    if on_warfarin and years >= 75:
        factors.append(
            Factor(
                "WARF_AGE75",
                9,
                "EHR_MEDICATIONS",
                on_warfarin[0].get("rx_id", member_id),
                f"Anticoagulated with {on_warfarin[0].get('drug_name')} at age {years}",
            )
        )
    if on_warfarin and on_nsaid:
        factors.append(
            Factor(
                "DDI_WARF_NSAID",
                15,
                "EHR_MEDICATIONS",
                f"{on_warfarin[0].get('rx_id')} + {on_nsaid[0].get('rx_id')}",
                f"Warfarin + NSAID ({on_nsaid[0].get('drug_name')}) both active",
            )
        )

    raw = sum(f.points for f in factors)
    score = min(100, raw)
    return {
        "member_id": member_id,
        "atri_score": score,
        "atri_score_uncapped": raw,
        "atri_tier": tier_for(score),
        "factors": [f.as_dict() for f in factors],
        "active_med_count": n_meds,
        "ed_visits_90d": len(ed_90),
        "last_a1c_value": last_a1c.get("value") if last_a1c else None,
        "last_a1c_date": last_a1c.get("result_date") if last_a1c else None,
        "allowed_12m": allowed,
        "has_dm": has_dm,
        "on_sglt2": any(med_norm(m.get("drug_name", "")).split()[0] in SGLT2_NAMES for m in active_meds),
    }
