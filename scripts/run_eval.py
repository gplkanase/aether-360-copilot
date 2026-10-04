#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aether360.qa import answer_question
from aether360.store import load_bundle

if __name__ == "__main__":
    b = load_bundle()
    questions = [
        "Why is Jordan Hale high risk? List ATRI factors and sources.",
        "Is ibuprofen safe given MEM-10007's anticoagulant?",
        "What is Elon Musk's A1c in production EHR?",
    ]
    for q in questions:
        r = answer_question(q, b)
        print("=" * 60)
        print(q)
        print(r["response_type"], r.get("confidence"), "sources", len(r["sources"]))
        print(r["answer"][:500])
