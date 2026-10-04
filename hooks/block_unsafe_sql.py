#!/usr/bin/env python3
"""CoCo PreToolUse hook: block destructive SQL and production-like PHI identifiers."""
from __future__ import annotations

import json
import re
import sys

BLOCK_PATTERNS = [
    (r"\bDROP\s+DATABASE\b", "Refusing DROP DATABASE in the Aether hackathon project."),
    (r"\bDROP\s+ACCOUNT\b", "Refusing DROP ACCOUNT."),
    (r"\bSSN\b|\bSOCIAL_SECURITY\b", "Refusing queries that look like real SSN fields."),
    (r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b", "Refusing SSN-shaped literals. Use synthetic MEM-* keys."),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}))
        return 0

    tool_input = payload.get("tool_input") or {}
    sql = " ".join(
        str(tool_input.get(k, ""))
        for k in ("sql", "command", "query", "statement")
    )
    blob = sql.upper() if sql else json.dumps(tool_input).upper()

    for pattern, reason in BLOCK_PATTERNS:
        if re.search(pattern, blob, flags=re.I):
            print(json.dumps({"decision": "block", "reason": reason}))
            return 2

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
