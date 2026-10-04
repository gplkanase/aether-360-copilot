"""Aether Care Ops MCP server (stdio, JSON-RPC 2.0).

Synthetic tickets only — stands in for Jira/ServiceNow so CoCo can take action.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STORE = Path(__file__).resolve().parent / ".ticket_store.json"


def _load() -> list[dict]:
    if STORE.exists():
        return json.loads(STORE.read_text(encoding="utf-8"))
    return []


def _save(rows: list[dict]) -> None:
    STORE.write_text(json.dumps(rows, indent=2), encoding="utf-8")


TOOLS = [
    {
        "name": "open_care_gap_ticket",
        "description": "Open a synthetic care-management ticket for a member (Jira-shaped). Not a real Jira call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "member_id": {"type": "string", "description": "Synthetic member id, e.g. MEM-10007"},
                "reason": {"type": "string", "description": "Why the ticket is being opened"},
                "owner": {"type": "string", "description": "Queue: pharmacist, care_manager, utilization"},
            },
            "required": ["member_id", "reason"],
        },
    },
    {
        "name": "list_open_tickets",
        "description": "List synthetic care-ops tickets stored locally.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "post_safety_review",
        "description": "Log a safety review (warfarin/NSAID, SGLT2 ketosis, etc.) against a member.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "member_id": {"type": "string"},
                "flag_code": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["member_id", "flag_code", "summary"],
        },
    },
]


def _call(name: str, args: dict) -> dict:
    tickets = _load()
    if name == "open_care_gap_ticket":
        ticket = {
            "id": f"AETH-{len(tickets)+1:04d}",
            "type": "care_gap",
            "member_id": args.get("member_id"),
            "reason": args.get("reason"),
            "owner": args.get("owner") or "care_manager",
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tickets.append(ticket)
        _save(tickets)
        return ticket
    if name == "list_open_tickets":
        return {"tickets": [t for t in tickets if t.get("status") == "open"]}
    if name == "post_safety_review":
        ticket = {
            "id": f"SAFE-{len(tickets)+1:04d}",
            "type": "safety_review",
            "member_id": args.get("member_id"),
            "flag_code": args.get("flag_code"),
            "reason": args.get("summary"),
            "owner": "pharmacist",
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tickets.append(ticket)
        _save(tickets)
        return ticket
    raise ValueError(f"Unknown tool {name}")


def _reply(msg_id, result=None, error=None) -> None:
    payload: dict = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method")
        msg_id = req.get("id")
        if method == "initialize":
            _reply(
                msg_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aether-care-ops", "version": "1.0.0"},
                },
            )
            continue
        if method == "notifications/initialized":
            continue
        if method == "tools/list":
            _reply(msg_id, {"tools": TOOLS})
            continue
        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            try:
                result = _call(name, args)
                _reply(
                    msg_id,
                    {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
                )
            except Exception as exc:
                _reply(msg_id, error={"code": -32000, "message": str(exc)})
            continue
        if msg_id is not None:
            _reply(msg_id, error={"code": -32601, "message": f"Unknown method {method}"})


if __name__ == "__main__":
    main()
