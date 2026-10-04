from pathlib import Path

import yaml

from aether360.qa import answer_question
from aether360.store import load_bundle


def test_eval_questions():
    root = Path(__file__).resolve().parents[1]
    spec = yaml.safe_load((root / "tests" / "eval_questions.yaml").read_text(encoding="utf-8"))
    bundle = load_bundle()
    assert len(bundle.member_360) >= 36
    hale = bundle.member("MEM-10007")
    assert hale and hale["atri_tier"] == "Very High"

    for case in spec:
        result = answer_question(case["question"], bundle)
        assert result["response_type"] == case["expect"], (case["id"], result["response_type"], result["answer"][:200])
        blob = (result["answer"] + " " + str(result.get("sources"))).lower()
        for needle in case.get("must_include") or []:
            assert needle.lower() in blob, (case["id"], needle)
        if case["expect"] == "cited":
            assert result["sources"], case["id"]


def test_orphan_free_xwalk():
    bundle = load_bundle()
    members = {m["member_id"] for m in bundle.members}
    patients = {p["patient_id"] for p in bundle.patients}
    for row in bundle.xwalk:
        assert row["member_id"] in members
        assert row["patient_id"] in patients
