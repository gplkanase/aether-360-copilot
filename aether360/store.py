"""Load synthetic bronze CSVs and build gold Member 360 in memory."""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from aether360.risk import AS_OF, age_years, score_member
from aether360.retrieve import chunk_text

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "data" / "generated"
DOC_DIR = ROOT / "data" / "documents"


def _read(name: str) -> list[dict[str, Any]]:
    path = GEN / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _group(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[row[key]].append(row)
    return out


def _list_join(values: list[str]) -> str:
    return "; ".join(v for v in values if v)


@dataclass
class Bundle:
    as_of: str
    members: list[dict[str, Any]]
    patients: list[dict[str, Any]]
    xwalk: list[dict[str, Any]]
    coverage: list[dict[str, Any]]
    conditions: list[dict[str, Any]]
    medications: list[dict[str, Any]]
    encounters: list[dict[str, Any]]
    labs: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    rx_claims: list[dict[str, Any]]
    manifest: list[dict[str, Any]]
    member_360: list[dict[str, Any]] = field(default_factory=list)
    atri_factors: list[dict[str, Any]] = field(default_factory=list)
    care_gaps: list[dict[str, Any]] = field(default_factory=list)
    safety_flags: list[dict[str, Any]] = field(default_factory=list)
    chunks: list[dict[str, Any]] = field(default_factory=list)
    documents: dict[str, str] = field(default_factory=dict)

    def member(self, member_id: str) -> dict[str, Any] | None:
        mid = member_id.upper()
        for row in self.member_360:
            if row["member_id"] == mid:
                return row
        return None

    def search_member(self, q: str) -> list[dict[str, Any]]:
        qn = (q or "").strip().lower()
        if not qn:
            return self.member_360
        hits = []
        for row in self.member_360:
            blob = " ".join(
                str(row.get(k, ""))
                for k in ("member_id", "patient_id", "full_name", "panel", "region")
            ).lower()
            if qn in blob:
                hits.append(row)
        return hits


def _build_gold(bundle: Bundle) -> None:
    cond_g = _group(bundle.conditions, "member_id")
    med_g = _group(bundle.medications, "member_id")
    enc_g = _group(bundle.encounters, "member_id")
    lab_g = _group(bundle.labs, "member_id")
    clm_g = _group(bundle.claims, "member_id")
    cov_g = _group(bundle.coverage, "member_id")
    xwalk = {r["member_id"]: r["patient_id"] for r in bundle.xwalk}

    gold = []
    factors = []
    gaps = []
    flags = []
    for m in bundle.members:
        mid = m["member_id"]
        scored = score_member(
            m,
            cond_g.get(mid, []),
            med_g.get(mid, []),
            enc_g.get(mid, []),
            lab_g.get(mid, []),
            clm_g.get(mid, []),
        )
        active_dx = [
            f"{c['icd10']} {c['description']}"
            for c in cond_g.get(mid, [])
            if c.get("status") == "active"
        ]
        active_rx = [
            f"{rx['drug_name']} ({rx['sig']})"
            for rx in med_g.get(mid, [])
            if rx.get("status") == "active"
        ]
        last_enc = max(
            (e.get("start_date") or "" for e in enc_g.get(mid, [])),
            default="",
        )
        factor_codes = [f["factor_code"] for f in scored["factors"]]
        open_gaps = []
        if "GAP_A1C" in factor_codes:
            open_gaps.append("GSD-A1c overdue")
            gaps.append(
                {
                    "member_id": mid,
                    "measure": "GSD-A1c",
                    "status": "open",
                    "evidence": next(f["evidence"] for f in scored["factors"] if f["factor_code"] == "GAP_A1C"),
                }
            )
        if "GAP_PCP" in factor_codes:
            open_gaps.append("No PCP 12m")
            gaps.append(
                {
                    "member_id": mid,
                    "measure": "PCP-12m",
                    "status": "open",
                    "evidence": "No ambulatory encounter in 12 months",
                }
            )
        if "GAP_STATIN_CAD" in factor_codes:
            open_gaps.append("CAD without statin")
            gaps.append(
                {
                    "member_id": mid,
                    "measure": "CAD-statin",
                    "status": "open",
                    "evidence": "CAD without active statin",
                }
            )
        safety = []
        if "DDI_WARF_NSAID" in factor_codes:
            safety.append("Warfarin + NSAID")
            flags.append(
                {
                    "member_id": mid,
                    "flag_code": "DDI_WARF_NSAID",
                    "severity": "high",
                    "evidence": next(f["evidence"] for f in scored["factors"] if f["factor_code"] == "DDI_WARF_NSAID"),
                }
            )
        if scored.get("on_sglt2"):
            safety.append("SGLT2 on profile — ketosis counseling")
            flags.append(
                {
                    "member_id": mid,
                    "flag_code": "SGLT2_KETOSIS_WATCH",
                    "severity": "moderate",
                    "evidence": "Active SGLT2 inhibitor",
                }
            )
        cov = (cov_g.get(mid) or [{}])[0]
        gold.append(
            {
                "member_id": mid,
                "patient_id": xwalk.get(mid, ""),
                "full_name": f"{m['first_name']} {m['last_name']}",
                "first_name": m["first_name"],
                "last_name": m["last_name"],
                "dob": m["dob"],
                "age_years": age_years(m["dob"]),
                "sex": m["sex"],
                "region": m["region"],
                "line_of_business": m["line_of_business"],
                "panel": m["panel"],
                "pcp_name": m["pcp_name"],
                "plan_id": m["plan_id"],
                "product_name": cov.get("product_name", ""),
                "has_metabolic_rider": cov.get("has_metabolic_rider", "false"),
                "atri_score": scored["atri_score"],
                "atri_score_uncapped": scored["atri_score_uncapped"],
                "atri_tier": scored["atri_tier"],
                "active_condition_list": _list_join(active_dx),
                "active_med_list": _list_join(active_rx),
                "active_med_count": scored["active_med_count"],
                "ed_visits_90d": scored["ed_visits_90d"],
                "readmit_30d_flag": any(
                    str(e.get("unplanned_readmit_30d")).lower() == "true" for e in enc_g.get(mid, [])
                ),
                "open_gap_list": _list_join(open_gaps),
                "safety_flag_list": _list_join(safety),
                "last_encounter_date": last_enc,
                "last_a1c_value": scored["last_a1c_value"],
                "last_a1c_date": scored["last_a1c_date"],
                "allowed_12m": scored["allowed_12m"],
                "as_of": AS_OF.isoformat(),
            }
        )
        for f in scored["factors"]:
            factors.append({"member_id": mid, **f})

    bundle.member_360 = sorted(gold, key=lambda r: (-r["atri_score"], r["member_id"]))
    bundle.atri_factors = factors
    bundle.care_gaps = gaps
    bundle.safety_flags = flags


def _build_chunks(bundle: Bundle) -> None:
    docs: dict[str, str] = {}
    chunks: list[dict[str, Any]] = []
    for row in bundle.manifest:
        path = DOC_DIR / row["filename"]
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        docs[row["doc_id"]] = text
        for i, chunk in enumerate(chunk_text(text), start=1):
            chunks.append(
                {
                    "chunk_id": f"{row['doc_id']}-c{i:02d}",
                    "doc_id": row["doc_id"],
                    "document_class": row["document_class"],
                    "title": row["title"],
                    "member_id": row.get("member_id") or "",
                    "service_date": row.get("service_date") or "",
                    "note_type": row.get("note_type") or "",
                    "chunk_index": i,
                    "text": chunk,
                }
            )
    bundle.documents = docs
    bundle.chunks = chunks


@lru_cache(maxsize=1)
def load_bundle() -> Bundle:
    bundle = Bundle(
        as_of=AS_OF.isoformat(),
        members=_read("payer_members.csv"),
        patients=_read("ehr_patients.csv"),
        xwalk=_read("member_patient_xwalk.csv"),
        coverage=_read("coverage.csv"),
        conditions=_read("ehr_conditions.csv"),
        medications=_read("ehr_medications.csv"),
        encounters=_read("ehr_encounters.csv"),
        labs=_read("ehr_labs.csv"),
        claims=_read("payer_medical_claims.csv"),
        rx_claims=_read("payer_pharmacy_claims.csv"),
        manifest=_read("doc_manifest.csv"),
    )
    _build_gold(bundle)
    _build_chunks(bundle)
    return bundle
