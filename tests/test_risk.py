from aether360.risk import score_member, tier_for


def _member(**kwargs):
    base = {
        "member_id": "MEM-10007",
        "dob": "1948-03-11",
    }
    base.update(kwargs)
    return base


def test_hale_is_very_high():
    member = _member()
    conditions = [
        {"icd10": "I50.22", "description": "CHF", "status": "active"},
        {"icd10": "N18.3", "description": "CKD3", "status": "active"},
        {"icd10": "E11.9", "description": "T2DM", "status": "active"},
        {"icd10": "I48.91", "description": "AFib", "status": "active"},
    ]
    meds = [
        {"rx_id": "Rx-4412", "drug_name": "warfarin", "status": "active"},
        {"rx_id": "Rx-4413", "drug_name": "carvedilol", "status": "active"},
        {"rx_id": "Rx-4414", "drug_name": "furosemide", "status": "active"},
        {"rx_id": "Rx-4415", "drug_name": "lisinopril", "status": "active"},
        {"rx_id": "Rx-4416", "drug_name": "metformin", "status": "active"},
        {"rx_id": "Rx-4417", "drug_name": "insulin glargine", "status": "active"},
        {"rx_id": "Rx-4418", "drug_name": "spironolactone", "status": "active"},
        {"rx_id": "Rx-4419", "drug_name": "ibuprofen", "status": "active"},
    ]
    encounters = [
        {
            "encounter_id": "ENC-7002",
            "encounter_class": "inpatient",
            "start_date": "2026-07-12",
            "unplanned_readmit_30d": "true",
        },
        {
            "encounter_id": "ENC-7004",
            "encounter_class": "emergency",
            "start_date": "2026-05-02",
            "unplanned_readmit_30d": "false",
        },
        {
            "encounter_id": "ENC-7003",
            "encounter_class": "ambulatory",
            "start_date": "2026-07-20",
            "unplanned_readmit_30d": "false",
        },
    ]
    labs = [{"lab_id": "LAB-07-A1C", "loinc": "4548-4", "test_code": "A1C", "value": "8.4", "result_date": "2025-10-01"}]
    claims = [{"allowed_amount": 87300}]
    scored = score_member(member, conditions, meds, encounters, labs, claims)
    codes = {f["factor_code"] for f in scored["factors"]}
    assert "DDI_WARF_NSAID" in codes
    assert "READMIT_30D" in codes
    assert "HCC_CHF" in codes
    assert scored["atri_tier"] == "Very High"
    assert scored["atri_score"] == min(100, scored["atri_score_uncapped"])


def test_tier_boundaries():
    assert tier_for(19) == "Low"
    assert tier_for(20) == "Moderate"
    assert tier_for(59) == "High"
    assert tier_for(60) == "Very High"


def test_statin_gap_only_with_cad():
    member = _member(member_id="MEM-10021", dob="1972-01-19")
    conditions = [{"icd10": "I25.10", "description": "CAD", "status": "active"}]
    meds = [{"rx_id": "Rx-1", "drug_name": "aspirin", "status": "active"}]
    encounters = [
        {
            "encounter_id": "E1",
            "encounter_class": "ambulatory",
            "start_date": "2026-06-18",
            "unplanned_readmit_30d": "false",
        }
    ]
    scored = score_member(member, conditions, meds, encounters, [], [])
    assert any(f["factor_code"] == "GAP_STATIN_CAD" for f in scored["factors"])
