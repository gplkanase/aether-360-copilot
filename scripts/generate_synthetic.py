#!/usr/bin/env python3
"""Generate referentially consistent synthetic EHR, claims, and documents.

All people, claims, notes, and labels are fictional. Safe for hackathon demos.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generated"
DOC_DIR = ROOT / "data" / "documents"
AS_OF = date(2026, 8, 31)
SEED = 360

FIRST = [
    "Jordan", "River", "Avery", "Samira", "Ellis", "Morgan", "Kai", "Noor",
    "Quinn", "Rowan", "Sasha", "Tomas", "Uma", "Val", "Wren", "Yara",
    "Zion", "Blake", "Cameron", "Drew", "Emery", "Finley", "Gray", "Harper",
    "Indigo", "Jules", "Kendall", "Logan", "Marley", "Nico",
]
LAST = [
    "Hale", "Chen", "Okonkwo", "Patel", "Navarro", "Blake", "Ibarra", "Hassan",
    "Singh", "Nguyen", "Brooks", "Almeida", "Okafor", "Berg", "Diaz", "Khan",
    "Sato", "Mwangi", "Cohen", "Walsh", "Park", "Rossi", "Novak", "Silva",
    "Andersen", "Qureshi", "Vogel", "Laurent", "Kowalski", "Bennett",
]
REGIONS = ["North Lake", "River District", "Summit County"]
LOBS = ["Medicare Advantage", "Commercial", "Dual"]
PANELS = ["Heart Failure", "Diabetes", "COPD", "General"]
PCPS = ["Dr. Priya Raman", "Dr. Luis Ortega", "Dr. Hannah Cho", "Dr. Amare Bekele"]

GEN_CONDITIONS = [
    ("I10", "Essential hypertension"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("E66.9", "Obesity, unspecified"),
    ("J44.9", "COPD, unspecified"),
    ("I25.10", "CAD of native artery without angina"),
    ("F32.9", "Major depressive disorder, unspecified"),
    ("M54.5", "Low back pain"),
    ("E78.5", "Hyperlipidemia, unspecified"),
]
GEN_MEDS = [
    ("lisinopril", "ACE inhibitor", "10 mg PO daily"),
    ("metformin", "biguanide", "1000 mg PO BID"),
    ("atorvastatin", "statin", "40 mg PO nightly"),
    ("amlodipine", "CCB", "5 mg PO daily"),
    ("sertraline", "SSRI", "50 mg PO daily"),
    ("albuterol", "SABA", "2 puffs q4h PRN"),
    ("omeprazole", "PPI", "20 mg PO daily"),
    ("levothyroxine", "thyroid", "75 mcg PO daily"),
]


def daterange_back(days: int) -> date:
    return AS_OF - timedelta(days=days)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    names = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=names, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def hero_members() -> list[dict]:
    return [
        {
            "member_id": "MEM-10007",
            "patient_id": "PAT-10007",
            "first_name": "Jordan",
            "last_name": "Hale",
            "dob": "1948-03-11",
            "sex": "F",
            "region": "North Lake",
            "line_of_business": "Medicare Advantage",
            "panel": "Heart Failure",
            "pcp_name": "Dr. Priya Raman",
            "plan_id": "AETHER-MA-GOLD",
            "hero": True,
        },
        {
            "member_id": "MEM-10014",
            "patient_id": "PAT-10014",
            "first_name": "River",
            "last_name": "Chen",
            "dob": "1964-07-22",
            "sex": "M",
            "region": "River District",
            "line_of_business": "Commercial",
            "panel": "Diabetes",
            "pcp_name": "Dr. Luis Ortega",
            "plan_id": "AETHER-COM-PLUS",
            "hero": True,
        },
        {
            "member_id": "MEM-10021",
            "patient_id": "PAT-10021",
            "first_name": "Avery",
            "last_name": "Okonkwo",
            "dob": "1972-01-19",
            "sex": "F",
            "region": "Summit County",
            "line_of_business": "Commercial",
            "panel": "General",
            "pcp_name": "Dr. Hannah Cho",
            "plan_id": "AETHER-COM-PLUS",
            "hero": True,
        },
        {
            "member_id": "MEM-10003",
            "patient_id": "PAT-10003",
            "first_name": "Samira",
            "last_name": "Patel",
            "dob": "1956-09-03",
            "sex": "F",
            "region": "North Lake",
            "line_of_business": "Medicare Advantage",
            "panel": "COPD",
            "pcp_name": "Dr. Amare Bekele",
            "plan_id": "AETHER-MA-GOLD",
            "hero": True,
        },
        {
            "member_id": "MEM-10031",
            "patient_id": "PAT-10031",
            "first_name": "Ellis",
            "last_name": "Navarro",
            "dob": "1981-11-30",
            "sex": "M",
            "region": "River District",
            "line_of_business": "Commercial",
            "panel": "Diabetes",
            "pcp_name": "Dr. Luis Ortega",
            "plan_id": "AETHER-COM-PLUS",
            "hero": True,
        },
        {
            "member_id": "MEM-10018",
            "patient_id": "PAT-10018",
            "first_name": "Morgan",
            "last_name": "Blake",
            "dob": "1992-04-17",
            "sex": "F",
            "region": "Summit County",
            "line_of_business": "Commercial",
            "panel": "General",
            "pcp_name": "Dr. Hannah Cho",
            "plan_id": "AETHER-COM-PLUS",
            "hero": True,
        },
    ]


def generated_members(rng: random.Random, n: int = 30, start: int = 20001) -> list[dict]:
    used_names = {(m["first_name"], m["last_name"]) for m in hero_members()}
    rows = []
    i = 0
    while len(rows) < n:
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        if (fn, ln) in used_names:
            i += 1
            continue
        used_names.add((fn, ln))
        mid = start + len(rows)
        age = rng.randint(34, 88)
        dob = date(AS_OF.year - age, rng.randint(1, 12), rng.randint(1, 28))
        lob = rng.choices(LOBS, weights=[0.45, 0.4, 0.15])[0]
        panel = rng.choice(PANELS)
        rows.append(
            {
                "member_id": f"MEM-{mid}",
                "patient_id": f"PAT-{mid}",
                "first_name": fn,
                "last_name": ln,
                "dob": dob.isoformat(),
                "sex": rng.choice(["F", "M"]),
                "region": rng.choice(REGIONS),
                "line_of_business": lob,
                "panel": panel,
                "pcp_name": rng.choice(PCPS),
                "plan_id": "AETHER-MA-GOLD" if "Medicare" in lob or lob == "Dual" else "AETHER-COM-PLUS",
                "hero": False,
            }
        )
    return rows


def hero_clinical() -> dict[str, list[dict]]:
    conditions = [
        _cond("MEM-10007", "PAT-10007", "I50.22", "Chronic systolic (congestive) heart failure"),
        _cond("MEM-10007", "PAT-10007", "N18.3", "Chronic kidney disease, stage 3"),
        _cond("MEM-10007", "PAT-10007", "E11.9", "Type 2 diabetes mellitus without complications"),
        _cond("MEM-10007", "PAT-10007", "I48.91", "Unspecified atrial fibrillation"),
        _cond("MEM-10007", "PAT-10007", "I10", "Essential hypertension"),
        _cond("MEM-10014", "PAT-10014", "E11.9", "Type 2 diabetes mellitus without complications"),
        _cond("MEM-10014", "PAT-10014", "E66.9", "Obesity, unspecified"),
        _cond("MEM-10014", "PAT-10014", "I10", "Essential hypertension"),
        _cond("MEM-10021", "PAT-10021", "I25.10", "CAD of native artery without angina"),
        _cond("MEM-10021", "PAT-10021", "I10", "Essential hypertension"),
        _cond("MEM-10003", "PAT-10003", "J44.1", "COPD with acute exacerbation"),
        _cond("MEM-10003", "PAT-10003", "F32.1", "Major depressive disorder, single episode, moderate"),
        _cond("MEM-10003", "PAT-10003", "I10", "Essential hypertension"),
        _cond("MEM-10031", "PAT-10031", "E66.9", "Obesity, unspecified"),
        _cond("MEM-10031", "PAT-10031", "E11.9", "Type 2 diabetes mellitus without complications"),
        _cond("MEM-10018", "PAT-10018", "I10", "Essential hypertension"),
    ]
    meds = [
        _med("MEM-10007", "Rx-4412", "warfarin", "anticoagulant", "5 mg PO daily", "2024-11-02"),
        _med("MEM-10007", "Rx-4413", "carvedilol", "beta blocker", "12.5 mg PO BID", "2023-01-15"),
        _med("MEM-10007", "Rx-4414", "furosemide", "loop diuretic", "40 mg PO BID", "2023-01-15"),
        _med("MEM-10007", "Rx-4415", "lisinopril", "ACE inhibitor", "20 mg PO daily", "2022-06-01"),
        _med("MEM-10007", "Rx-4416", "metformin", "biguanide", "500 mg PO BID", "2021-04-10"),
        _med("MEM-10007", "Rx-4417", "insulin glargine", "basal insulin", "18 units SQ nightly", "2025-02-01"),
        _med("MEM-10007", "Rx-4418", "spironolactone", "MRA", "25 mg PO daily", "2023-01-15"),
        _med("MEM-10007", "Rx-4419", "ibuprofen", "NSAID", "400 mg PO TID PRN dental pain", "2026-07-18"),
        _med("MEM-10014", "Rx-5510", "empagliflozin", "SGLT2 inhibitor", "10 mg PO daily", "2025-09-12"),
        _med("MEM-10014", "Rx-5511", "metformin", "biguanide", "1000 mg PO BID", "2020-03-01"),
        _med("MEM-10014", "Rx-5512", "lisinopril", "ACE inhibitor", "10 mg PO daily", "2021-08-19"),
        _med("MEM-10021", "Rx-6610", "aspirin", "antiplatelet", "81 mg PO daily", "2019-11-11"),
        _med("MEM-10021", "Rx-6611", "metoprolol succinate", "beta blocker", "50 mg PO daily", "2024-02-02"),
        _med("MEM-10003", "Rx-3310", "albuterol", "SABA", "2 puffs q4h PRN", "2018-05-05"),
        _med("MEM-10003", "Rx-3311", "fluticasone-salmeterol", "ICS/LABA", "250/50 1 puff BID", "2022-09-09"),
        _med("MEM-10003", "Rx-3312", "sertraline", "SSRI", "50 mg PO daily", "2024-01-20"),
        _med("MEM-10031", "Rx-7710", "metformin", "biguanide", "1000 mg PO BID", "2023-06-06"),
        _med("MEM-10018", "Rx-2210", "lisinopril", "ACE inhibitor", "10 mg PO daily", "2025-01-08"),
    ]
    enc = [
        _enc("ENC-7001", "MEM-10007", "PAT-10007", "inpatient", "2026-06-10", "2026-06-14", "CHF exacerbation", False, 48200),
        _enc("ENC-7002", "MEM-10007", "PAT-10007", "inpatient", "2026-07-12", "2026-07-16", "Volume overload, unplanned readmit", True, 39100),
        _enc("ENC-7003", "MEM-10007", "PAT-10007", "ambulatory", "2026-07-20", "2026-07-20", "PCP post-discharge", False, 240),
        _enc("ENC-7004", "MEM-10007", "PAT-10007", "emergency", "2026-05-02", "2026-05-02", "Dyspnea", False, 2100),
        _enc("ENC-1401", "MEM-10014", "PAT-10014", "emergency", "2026-08-02", "2026-08-02", "Nausea, possible ketosis", False, 1800),
        _enc("ENC-1402", "MEM-10014", "PAT-10014", "ambulatory", "2026-08-05", "2026-08-05", "Diabetes follow-up", False, 220),
        _enc("ENC-1403", "MEM-10014", "PAT-10014", "ambulatory", "2026-03-11", "2026-03-11", "PCP", False, 210),
        _enc("ENC-2101", "MEM-10021", "PAT-10021", "ambulatory", "2026-06-18", "2026-06-18", "Cardiology CAD follow-up", False, 310),
        _enc("ENC-0301", "MEM-10003", "PAT-10003", "emergency", "2026-06-21", "2026-06-21", "COPD flare", False, 2400),
        _enc("ENC-0302", "MEM-10003", "PAT-10003", "emergency", "2026-07-08", "2026-07-08", "COPD flare", False, 2600),
        _enc("ENC-0303", "MEM-10003", "PAT-10003", "emergency", "2026-08-04", "2026-08-04", "COPD flare", False, 2550),
        _enc("ENC-0304", "MEM-10003", "PAT-10003", "ambulatory", "2026-04-02", "2026-04-02", "Pulmonary clinic", False, 280),
        _enc("ENC-3101", "MEM-10031", "PAT-10031", "ambulatory", "2026-08-12", "2026-08-12", "Weight and glycemic visit", False, 230),
        _enc("ENC-1801", "MEM-10018", "PAT-10018", "ambulatory", "2026-05-14", "2026-05-14", "Annual wellness", False, 190),
    ]
    labs = [
        _lab("LAB-07-A1C", "MEM-10007", "PAT-10007", "4548-4", "A1C", "8.4", "%", "2025-10-01"),
        _lab("LAB-07-GFR", "MEM-10007", "PAT-10007", "33914-3", "eGFR", "48", "mL/min/1.73m2", "2026-07-13"),
        _lab("LAB-07-INR", "MEM-10007", "PAT-10007", "6301-6", "INR", "2.4", "ratio", "2026-07-21"),
        _lab("LAB-14-A1C", "MEM-10014", "PAT-10014", "4548-4", "A1C", "7.9", "%", "2026-07-01"),
        _lab("LAB-14-KET", "MEM-10014", "PAT-10014", "2514-8", "Urine ketones", "1+", "qual", "2026-08-02"),
        _lab("LAB-21-LDL", "MEM-10021", "PAT-10021", "13457-7", "LDL", "142", "mg/dL", "2026-06-18"),
        _lab("LAB-03-A1C", "MEM-10003", "PAT-10003", "4548-4", "A1C", "5.8", "%", "2026-04-02"),
        _lab("LAB-31-A1C", "MEM-10031", "PAT-10031", "4548-4", "A1C", "8.1", "%", "2026-08-12"),
        _lab("LAB-18-A1C", "MEM-10018", "PAT-10018", "4548-4", "A1C", "5.2", "%", "2026-05-14"),
    ]
    return {"conditions": conditions, "medications": meds, "encounters": enc, "labs": labs}


def _cond(member_id, patient_id, icd, desc, status="active"):
    return {
        "condition_id": f"DX-{member_id}-{icd}",
        "member_id": member_id,
        "patient_id": patient_id,
        "icd10": icd,
        "description": desc,
        "status": status,
        "onset_date": "2020-01-15",
        "source_system": "EHR",
    }


def _med(member_id, rx_id, drug, cls, sig, start):
    return {
        "rx_id": rx_id,
        "member_id": member_id,
        "patient_id": member_id.replace("MEM", "PAT"),
        "drug_name": drug,
        "drug_class": cls,
        "sig": sig,
        "status": "active",
        "start_date": start,
        "prescriber": "Dr. Priya Raman",
        "source_system": "EHR",
    }


def _enc(eid, member_id, patient_id, klass, start, end, reason, readmit, allowed):
    return {
        "encounter_id": eid,
        "member_id": member_id,
        "patient_id": patient_id,
        "encounter_class": klass,
        "start_date": start,
        "end_date": end,
        "reason": reason,
        "unplanned_readmit_30d": "true" if readmit else "false",
        "facility": "Aether North Lake Medical Center",
        "source_system": "EHR",
        "allowed_hint": allowed,
    }


def _lab(lid, member_id, patient_id, loinc, name, value, units, dt):
    return {
        "lab_id": lid,
        "member_id": member_id,
        "patient_id": patient_id,
        "loinc": loinc,
        "test_code": "A1C" if loinc == "4548-4" else name,
        "test_name": name,
        "value": value,
        "units": units,
        "result_date": dt,
        "source_system": "EHR",
    }


def fill_generated_clinical(members: list[dict], rng: random.Random) -> dict[str, list[dict]]:
    conditions, meds, enc, labs, claims = [], [], [], [], []
    rx_n = 9000
    enc_n = 8000
    lab_n = 8000
    clm_n = 8000
    for m in members:
        mid, pid = m["member_id"], m["patient_id"]
        k = rng.randint(1, 3)
        picked = rng.sample(GEN_CONDITIONS, k=k)
        for icd, desc in picked:
            conditions.append(_cond(mid, pid, icd, desc))
        med_k = rng.randint(1, 4)
        for drug, cls, sig in rng.sample(GEN_MEDS, k=med_k):
            rx_n += 1
            meds.append(_med(mid, f"Rx-{rx_n}", drug, cls, sig, "2024-02-02"))
        # ensure diabetes has A1c
        has_dm = any(c.startswith("E11") for c, _ in picked)
        last_pcp = AS_OF - timedelta(days=rng.randint(20, 400))
        enc_n += 1
        enc.append(
            _enc(
                f"ENC-{enc_n}",
                mid,
                pid,
                "ambulatory",
                last_pcp.isoformat(),
                last_pcp.isoformat(),
                "PCP visit",
                False,
                rng.randint(160, 280),
            )
        )
        if rng.random() < 0.25:
            ed = AS_OF - timedelta(days=rng.randint(5, 80))
            enc_n += 1
            enc.append(
                _enc(
                    f"ENC-{enc_n}",
                    mid,
                    pid,
                    "emergency",
                    ed.isoformat(),
                    ed.isoformat(),
                    "Acute visit",
                    False,
                    rng.randint(900, 3200),
                )
            )
        if has_dm or rng.random() < 0.5:
            lab_n += 1
            lab_dt = AS_OF - timedelta(days=rng.randint(30, 400 if has_dm else 200))
            labs.append(
                _lab(
                    f"LAB-{lab_n}",
                    mid,
                    pid,
                    "4548-4",
                    "A1C",
                    f"{rng.uniform(5.2, 9.1):.1f}",
                    "%",
                    lab_dt.isoformat(),
                )
            )
        clm_n += 1
        claims.append(_claim(f"CLM-{clm_n}", mid, last_pcp.isoformat(), "99213", rng.randint(160, 400), "11"))
    return {
        "conditions": conditions,
        "medications": meds,
        "encounters": enc,
        "labs": labs,
        "claims": claims,
    }


def _claim(cid, member_id, dt, cpt, allowed, pos):
    return {
        "claim_id": cid,
        "member_id": member_id,
        "claim_date": dt,
        "cpt": cpt,
        "dx_principal": "",
        "allowed_amount": allowed,
        "place_of_service": pos,
        "claim_type": "professional",
        "source_system": "CLAIMS",
    }


def hero_claims() -> list[dict]:
    rows = []
    mapping = [
        ("CLM-7001", "MEM-10007", "2026-06-10", "99223", 48200, "21", "I50.22"),
        ("CLM-7002", "MEM-10007", "2026-07-12", "99223", 39100, "21", "I50.22"),
        ("CLM-7003", "MEM-10007", "2026-07-20", "99214", 240, "11", "I50.22"),
        ("CLM-1401", "MEM-10014", "2026-08-02", "99285", 1800, "23", "E11.9"),
        ("CLM-2101", "MEM-10021", "2026-06-18", "99214", 310, "11", "I25.10"),
        ("CLM-0301", "MEM-10003", "2026-06-21", "99285", 2400, "23", "J44.1"),
        ("CLM-0302", "MEM-10003", "2026-07-08", "99285", 2600, "23", "J44.1"),
        ("CLM-0303", "MEM-10003", "2026-08-04", "99285", 2550, "23", "J44.1"),
        ("CLM-3101", "MEM-10031", "2026-08-12", "99214", 230, "11", "E66.9"),
        ("CLM-1801", "MEM-10018", "2026-05-14", "99395", 190, "11", "I10"),
    ]
    for cid, mid, dt, cpt, amt, pos, dx in mapping:
        r = _claim(cid, mid, dt, cpt, amt, pos)
        r["dx_principal"] = dx
        rows.append(r)
    rows.append(
        {
            "claim_id": "RXC-4412",
            "member_id": "MEM-10007",
            "claim_date": "2026-07-01",
            "cpt": "NDC-warfarin",
            "dx_principal": "I48.91",
            "allowed_amount": 18,
            "place_of_service": "01",
            "claim_type": "pharmacy",
            "source_system": "CLAIMS",
        }
    )
    return rows


def write_regulatory_docs() -> list[dict]:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        (
            "DOC-FDA-WARFARIN",
            "fda_label",
            "SYNTHETIC LABEL: Warfarin Sodium Tablets (Aether-labeled stand-in)",
            "DOC-FDA-WARFARIN.md",
            WARFARIN_LABEL,
        ),
        (
            "DOC-FDA-METFORAX",
            "fda_label",
            "SYNTHETIC LABEL: Metforax (metformin hydrochloride) tablets",
            "DOC-FDA-METFORAX.md",
            METFORAX_LABEL,
        ),
        (
            "DOC-FDA-CANAGLO",
            "fda_label",
            "SYNTHETIC LABEL: Canaglo (canagliflozin) tablets",
            "DOC-FDA-CANAGLO.md",
            CANAGLO_LABEL,
        ),
        (
            "DOC-SAFETY-SGLT2-DKA",
            "safety_alert",
            "Aether Safety Communication: SGLT2 inhibitors and euglycemic DKA",
            "DOC-SAFETY-SGLT2-DKA.md",
            SGLT2_ALERT,
        ),
        (
            "DOC-CMS-NCD-CGM",
            "cms_ncd",
            "SYNTHETIC CMS-style NCD: Continuous Glucose Monitors",
            "DOC-CMS-NCD-CGM.md",
            CMS_CGM,
        ),
        (
            "DOC-PA-GLP1",
            "pa_policy",
            "Aether Care 2026 Prior Authorization: GLP-1 receptor agonists",
            "DOC-PA-GLP1.md",
            PA_GLP1,
        ),
        (
            "DOC-FORMULARY-2026",
            "formulary",
            "Aether Care Alliance Formulary Excerpt 2026",
            "DOC-FORMULARY-2026.md",
            FORMULARY,
        ),
        (
            "DOC-HEDIS-GSD",
            "quality_spec",
            "Synthetic HEDIS GSD (Glycemic Status Assessment) spec excerpt",
            "DOC-HEDIS-GSD.md",
            HEDIS_GSD,
        ),
    ]
    manifest = []
    for doc_id, klass, title, fname, body in specs:
        path = DOC_DIR / fname
        path.write_text(body.strip() + "\n", encoding="utf-8")
        manifest.append(
            {
                "doc_id": doc_id,
                "document_class": klass,
                "title": title,
                "filename": fname,
                "member_id": "",
                "service_date": "2026-01-15",
                "note_type": "",
            }
        )
    return manifest


def write_clinical_notes() -> list[dict]:
    notes = [
        (
            "DOC-NOTE-7002",
            "MEM-10007",
            "discharge_summary",
            "2026-07-16",
            "DOC-NOTE-HALE-READMIT.md",
            NOTE_HALE_DC,
        ),
        (
            "DOC-NOTE-7003",
            "MEM-10007",
            "progress_note",
            "2026-07-20",
            "DOC-NOTE-HALE-PCP.md",
            NOTE_HALE_PCP,
        ),
        (
            "DOC-NOTE-4412",
            "MEM-10007",
            "pharmacy_consult",
            "2026-07-21",
            "DOC-NOTE-HALE-PHARM.md",
            NOTE_HALE_PHARM,
        ),
        (
            "DOC-NOTE-1401",
            "MEM-10014",
            "ed_note",
            "2026-08-02",
            "DOC-NOTE-CHEN-ED.md",
            NOTE_CHEN_ED,
        ),
        (
            "DOC-NOTE-2101",
            "MEM-10021",
            "progress_note",
            "2026-06-18",
            "DOC-NOTE-OKONKWO-CARD.md",
            NOTE_OKONKWO,
        ),
        (
            "DOC-NOTE-0303",
            "MEM-10003",
            "ed_note",
            "2026-08-04",
            "DOC-NOTE-PATEL-ED.md",
            NOTE_PATEL,
        ),
        (
            "DOC-NOTE-3101",
            "MEM-10031",
            "progress_note",
            "2026-08-12",
            "DOC-NOTE-NAVARRO-GLP1.md",
            NOTE_NAVARRO,
        ),
        (
            "DOC-NOTE-1801",
            "MEM-10018",
            "progress_note",
            "2026-05-14",
            "DOC-NOTE-BLAKE-AWV.md",
            NOTE_BLAKE,
        ),
    ]
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for doc_id, member_id, ntype, dt, fname, body in notes:
        (DOC_DIR / fname).write_text(body.strip() + "\n", encoding="utf-8")
        manifest.append(
            {
                "doc_id": doc_id,
                "document_class": "clinical_note",
                "title": f"{ntype} {member_id}",
                "filename": fname,
                "member_id": member_id,
                "service_date": dt,
                "note_type": ntype,
            }
        )
    return manifest


WARFARIN_LABEL = """
# SYNTHETIC PRESCRIBING INFORMATION — Warfarin Sodium Tablets
**Not an FDA document. Created for Aether Care Alliance hackathon. Do not use in patient care.**

## Boxed warning
Warfarin sodium can cause major or fatal bleeding. Regular INR monitoring is required.

## Drug interactions — bleeding risk
Concomitant use of antiplatelet agents, thrombolytics, and **NSAIDs (including ibuprofen, naproxen, and ketorolac)**
increases the risk of gastrointestinal and intracranial bleeding. Avoid concomitant NSAIDs unless the benefit
outweighs bleeding risk and the member has close INR and symptom monitoring.

## Diet
Vitamin K intake should remain consistent. Abrupt changes in leafy green vegetables can move INR out of range.

## Renal impairment
Dose adjustments may be required. Coordinate with eGFR when other nephrotoxic agents are used.

## Counseling
Instruct patients to report black stools, unexplained bruising, or severe headache immediately.
"""

METFORAX_LABEL = """
# SYNTHETIC PRESCRIBING INFORMATION — Metforax (metformin hydrochloride)
**Not an FDA document. Synthetic stand-in for hackathon retrieval demos.**

## Indication
Adjunct to diet and exercise to improve glycemic control in adults with type 2 diabetes mellitus.

## Renal dosing
Do not initiate Metforax if eGFR is below 45 mL/min/1.73m2. Discontinue if eGFR later falls below 30.
Assess eGFR at least annually, and more often in older adults or those with CKD.

## Lactic acidosis
Rare. Risk rises with hypoxic states, dehydration, and advanced CKD.

## Drug interactions
Iodinated contrast: temporarily withhold Metforax at the time of contrast in patients with eGFR 30–60.
"""

CANAGLO_LABEL = """
# SYNTHETIC PRESCRIBING INFORMATION — Canaglo (canagliflozin)
**Synthetic SGLT2 label stand-in. Not real FDA text.**

## Boxed warning (synthetic)
Risk of lower limb amputation was observed in a historical trial program. Counsel on foot care.

## Ketoacidosis
SGLT2 inhibitors are associated with ketoacidosis, including **euglycemic DKA**. Consider ketone evaluation in
patients with nausea, vomiting, or malaise even when glucose is only modestly elevated. Interrupt therapy for
prolonged fasting, surgery, or acute illness.

## Volume depletion
Canaglo causes osmotic diuresis. Use caution in older adults and those on loop diuretics.
"""

SGLT2_ALERT = """
# Aether Safety Communication (synthetic) — SGLT2 inhibitors and euglycemic DKA
Issued 2026-03-01. Internal safety office, Aether Care Alliance.

## Signal
Post-marketing style reports in this synthetic corpus describe diabetic ketoacidosis with near-normal glucose
in members taking empagliflozin, dapagliflozin, or canagliflozin.

## Recommended action
1. Educate members to hold the SGLT2 during vomiting, poor oral intake, or planned procedures.
2. ED clinicians: check urine or serum ketones when an SGLT2-treated member presents with GI symptoms.
3. Do not restart until the acute illness has resolved and a clinician has reviewed the case.

## Cross-reference
See synthetic Canaglo label section "Ketoacidosis".
"""

CMS_CGM = """
# SYNTHETIC National Coverage Determination-style excerpt — CGM
**Not a real CMS NCD. Written so the copilot can cite coverage language.**

## Covered indications (demo)
Aether Plan covers personal continuous glucose monitoring when ALL of the following are documented:
1. Diagnosis of diabetes mellitus (type 1 or type 2) on the problem list.
2. Insulin treated, OR documented hypoglycemia unawareness, OR A1c above the member-specific target despite dual oral therapy.
3. The treating clinician has a visit note stating CGM will be used to adjust therapy.
4. Member (or caregiver) is able to hear/see alerts or has a documented workaround.

## Non-covered
Wellness CGM without diabetes diagnosis. Duplicate transmitters within the same 12-month window without malfunction documentation.

## Documentation
Prior authorization reviewers must cite the visit note date and the most recent A1c lab row.
"""

PA_GLP1 = """
# Aether Care 2026 Prior Authorization — GLP-1 receptor agonists
Policy ID PA-GLP1-2026. Synthetic utilization management rule.

## Preferred products
Formulary preferred: liraglutide. Non-preferred: semaglutide, tirzepatide (step through preferred unless contraindicated).

## Approval criteria (type 2 diabetes)
Approve 12 months if:
- ICD-10 E11.* is active; AND
- A1c ≥ 7.0% on a lab in the last 6 months; AND
- Member has tried metformin unless eGFR < 45 (see Metforax synthetic label); AND
- BMI is documented.

## Obesity-only requests
Deny unless the rider "Aether Metabolic Rider" is on the coverage row. Standard commercial plus does not cover obesity-only GLP-1.

## Quantity
30-day supply. Dose escalation must match labeled titration in the product monograph (not included here).
"""

FORMULARY = """
# Aether Care Alliance Formulary Excerpt 2026 (synthetic)

| Drug | Tier | PA | Notes |
| --- | --- | --- | --- |
| metformin | 1 | No | Preferred biguanide |
| empagliflozin | 2 | No | SGLT2; safety alert 2026-03-01 |
| canagliflozin | 3 | Yes | Non-preferred SGLT2 |
| warfarin | 1 | No | INR program required |
| ibuprofen Rx | 1 | No | Avoid with anticoagulants |
| atorvastatin | 1 | No | High-intensity option |
| semaglutide | 3 | Yes | See PA-GLP1-2026 |
| liraglutide | 2 | Yes | Preferred GLP-1 |
"""

HEDIS_GSD = """
# Synthetic quality spec — Glycemic Status Assessment (GSD stand-in)

## Eligible population
Members 18–75 with diabetes (E10 or E11) continuously enrolled in the measurement year.

## Numerator
Most recent glycemic status (A1c or GMI) in the measurement year.

## Gap definition used by Aether 360
If the most recent A1c (LOINC 4548-4) is older than 180 days on the as-of date, the member has an open GSD-style gap.
This is an operationalization for the copilot, not an NCQA submission file.
"""

NOTE_HALE_DC = """
# Discharge summary — Aether North Lake Medical Center (SYNTHETIC)
**Patient:** Jordan Hale | **MRN:** PAT-10007 | **Member:** MEM-10007
**Admit:** 2026-07-12 | **Discharge:** 2026-07-16 | **Encounter:** ENC-7002

## Hospital course
Ms. Hale is a 78-year-old with HFrEF, CKD stage 3, type 2 diabetes, and atrial fibrillation on warfarin who was
readmitted 28 days after a June CHF hospitalization with recurrent volume overload. She received IV furosemide
and a 4 kg diuresis. INR on arrival 2.1, discharge INR 2.3.

This admission meets criteria for an **unplanned 30-day readmission** related to heart failure.

## Discharge medications
warfarin 5 mg daily; carvedilol 12.5 mg BID; furosemide 40 mg BID; lisinopril 20 mg daily;
metformin 500 mg BID; insulin glargine 18 units nightly; spironolactone 25 mg daily.

## Follow-up
PCP Dr. Raman within 7 days. Teach back on daily weights. eGFR 48 on 2026-07-13 — metformin continued at reduced dose
per synthetic Metforax renal language (eGFR ≥45).
"""

NOTE_HALE_PCP = """
# PCP follow-up — Dr. Priya Raman (SYNTHETIC)
**Patient:** Jordan Hale | PAT-10007 | MEM-10007 | Date: 2026-07-20 | ENC-7003

Interval history: discharged 4 days ago. Weights stable. She reports a dental extraction on 2026-07-18.
The dentist advised **ibuprofen 400 mg three times daily as needed** for pain. She has taken four doses.

Assessment: High bleeding risk given age, warfarin, and NSAID. Advised acetaminophen first line. Will message
dentistry and pharmacy. Last A1c 8.4% on 2025-10-01 — overdue for glycemic assessment.

Plan: INR tomorrow. Stop ibuprofen if possible. Pharmacist consult ordered.
"""

NOTE_HALE_PHARM = """
# Clinical pharmacy consult — anticoagulation (SYNTHETIC)
**Patient:** Jordan Hale | MEM-10007 | Date: 2026-07-21

Indication: warfarin for AFib. INR 2.4 (in range). Drug-drug: **ibuprofen started 2026-07-18**.
The synthetic warfarin label states NSAIDs increase major bleeding risk and should be avoided unless benefit
outweighs risk. Recommended discontinue NSAID, use acetaminophen, and repeat INR in 3–5 days if any further NSAID doses.
Documented safety flag for care management.
"""

NOTE_CHEN_ED = """
# Emergency department note (SYNTHETIC)
**Patient:** River Chen | PAT-10014 | MEM-10014 | Date: 2026-08-02 | ENC-1401

62-year-old with T2DM on empagliflozin and metformin. Two days of nausea and poor oral intake. Glucose 168.
Urine ketones 1+. No frank acidosis on VBG. Concern for **evolving ketosis on SGLT2**.

Actions: held empagliflozin, fluids, follow-up 72 hours. Counseled using Aether SGLT2 safety communication:
hold SGLT2 during vomiting or starvation. Consider endocrine if ketones persist.
"""

NOTE_OKONKWO = """
# Cardiology progress note (SYNTHETIC)
**Patient:** Avery Okonkwo | PAT-10021 | MEM-10021 | Date: 2026-06-18

54-year-old with native-vessel CAD, last stent 2024 (synthetic history). On aspirin 81 mg and metoprolol XL 50 mg.
**Not on a statin** — she declined in 2025 due to muscle symptoms; no rechallenge documented. LDL 142 mg/dL today.

Plan: shared decision on rosuvastatin 5 mg or ezetimibe. This is a quality gap for CAD statin use in ATRI (GAP_STATIN_CAD).
"""

NOTE_PATEL = """
# ED note — COPD (SYNTHETIC)
**Patient:** Samira Patel | PAT-10003 | MEM-10003 | Date: 2026-08-04 | ENC-0303

Third ED visit in 90 days for dyspnea and wheeze. Peak flow reduced. Given nebulizers and steroids.
Depression screen PHQ-9 = 11, continues sertraline. Care management: frequent ED utilizer, COPD panel.
"""

NOTE_NAVARRO = """
# Endocrinology / PCP note (SYNTHETIC)
**Patient:** Ellis Navarro | PAT-10031 | MEM-10031 | Date: 2026-08-12

44-year-old with T2DM and obesity. A1c 8.1% today. On metformin 1000 mg BID, adherent. BMI 34.2.
Requests semaglutide for weight and glucose. Per PA-GLP1-2026, diabetes criteria may be met (E11, A1c ≥7, metformin trial).
Must still step through preferred liraglutide unless contraindicated. Coverage is not obesity-only.
"""

NOTE_BLAKE = """
# Annual wellness visit (SYNTHETIC)
**Patient:** Morgan Blake | PAT-10018 | MEM-10018 | Date: 2026-05-14

34-year-old with well-controlled hypertension on lisinopril 10 mg. A1c 5.2%. No ED visits. Low complexity panel.
"""


def build_coverage(members: list[dict]) -> list[dict]:
    rows = []
    for m in members:
        rows.append(
            {
                "coverage_id": f"COV-{m['member_id']}",
                "member_id": m["member_id"],
                "plan_id": m["plan_id"],
                "line_of_business": m["line_of_business"],
                "product_name": "Aether Gold MA" if "Medicare" in m["line_of_business"] or m["line_of_business"] == "Dual" else "Aether Commercial Plus",
                "effective_date": "2026-01-01",
                "term_date": "",
                "has_metabolic_rider": "true" if m["member_id"] == "MEM-10031" else "false",
            }
        )
    return rows


def build_pharmacy_claims(meds: list[dict]) -> list[dict]:
    rows = []
    for i, m in enumerate(meds, start=1):
        rows.append(
            {
                "rx_claim_id": f"RXC-{i:04d}",
                "member_id": m["member_id"],
                "fill_date": "2026-07-15",
                "drug_name": m["drug_name"],
                "days_supply": 30,
                "allowed_amount": 12 if m["drug_name"] in {"metformin", "lisinopril", "warfarin"} else 45,
                "source_system": "CLAIMS",
            }
        )
    return rows


def main() -> None:
    rng = random.Random(SEED)
    heroes = hero_members()
    generated = generated_members(rng, n=30)
    members = heroes + generated

    payer_members = []
    ehr_patients = []
    xwalk = []
    for m in members:
        payer_members.append(
            {
                "member_id": m["member_id"],
                "first_name": m["first_name"],
                "last_name": m["last_name"],
                "dob": m["dob"],
                "sex": m["sex"],
                "region": m["region"],
                "line_of_business": m["line_of_business"],
                "panel": m["panel"],
                "pcp_name": m["pcp_name"],
                "plan_id": m["plan_id"],
            }
        )
        ehr_patients.append(
            {
                "patient_id": m["patient_id"],
                "given_name": m["first_name"],
                "family_name": m["last_name"],
                "birth_date": m["dob"],
                "sex": m["sex"],
                "clinic_region": m["region"],
                "pcp_name": m["pcp_name"],
                "mrn": m["patient_id"],
            }
        )
        xwalk.append(
            {
                "member_id": m["member_id"],
                "patient_id": m["patient_id"],
                "match_method": "synthetic_deterministic",
                "match_confidence": 1.0,
            }
        )

    hero = hero_clinical()
    gen = fill_generated_clinical(generated, rng)

    conditions = hero["conditions"] + gen["conditions"]
    medications = hero["medications"] + gen["medications"]
    encounters = hero["encounters"] + gen["encounters"]
    labs = hero["labs"] + gen["labs"]
    claims = hero_claims() + gen["claims"]
    coverage = build_coverage(members)
    rx_claims = build_pharmacy_claims(medications)
    docs = write_regulatory_docs() + write_clinical_notes()

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "payer_members.csv", payer_members)
    write_csv(OUT / "ehr_patients.csv", ehr_patients)
    write_csv(OUT / "member_patient_xwalk.csv", xwalk)
    write_csv(OUT / "coverage.csv", coverage)
    write_csv(OUT / "ehr_conditions.csv", conditions)
    write_csv(OUT / "ehr_medications.csv", medications)
    write_csv(OUT / "ehr_encounters.csv", encounters)
    write_csv(OUT / "ehr_labs.csv", labs)
    write_csv(OUT / "payer_medical_claims.csv", claims)
    write_csv(OUT / "payer_pharmacy_claims.csv", rx_claims)
    write_csv(OUT / "doc_manifest.csv", docs)

    summary = {
        "as_of": AS_OF.isoformat(),
        "members": len(members),
        "conditions": len(conditions),
        "medications": len(medications),
        "encounters": len(encounters),
        "labs": len(labs),
        "claims": len(claims),
        "documents": len(docs),
        "synthetic": True,
        "phi": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
