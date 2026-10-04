"""Question checks: scope, synthetic-only, and abstain."""
from __future__ import annotations

import re
from typing import Any

REAL_PERSON_HINTS = re.compile(
    r"\b(elon musk|taylor swift|ssn|social security|my real patient|production ehr)\b",
    re.I,
)
OFF_TOPIC = re.compile(
    r"\b(write me a (python|javascript) scraper|hack into|exploit|bitcoin dump)\b",
    re.I,
)


def check_question(question: str) -> dict[str, Any]:
    q = (question or "").strip()
    if not q:
        return {"ok": False, "action": "abstain", "reason": "Empty question."}
    if REAL_PERSON_HINTS.search(q):
        return {
            "ok": False,
            "action": "refuse",
            "reason": "This copilot only answers over fully synthetic Aether Care data. It will not look up real people or production PHI.",
        }
    if OFF_TOPIC.search(q):
        return {
            "ok": False,
            "action": "refuse",
            "reason": "Out of scope. Ask a clinical, safety, coverage, or member-360 question about the synthetic corpus.",
        }
    return {"ok": True, "action": "allow", "reason": ""}
