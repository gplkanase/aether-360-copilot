import io
import json
import runpy
from pathlib import Path


def test_sql_hook_blocks_ssn_shaped_literal(monkeypatch):
    hook = Path(__file__).resolve().parents[1] / "hooks" / "block_unsafe_sql.py"
    payload = json.dumps({"tool_input": {"sql": "SELECT * FROM t WHERE ssn = '123-45-6789'"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    ns = runpy.run_path(str(hook), run_name="not_main")
    # execute main
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    rc = ns["main"]()
    assert rc == 2
    assert json.loads(buf.getvalue())["decision"] == "block"


def test_sql_hook_allows_member_select(monkeypatch):
    hook = Path(__file__).resolve().parents[1] / "hooks" / "block_unsafe_sql.py"
    ns = runpy.run_path(str(hook), run_name="not_main")
    payload = json.dumps({"tool_input": {"sql": "SELECT * FROM gold.member_360 WHERE member_id = 'MEM-10007'"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    rc = ns["main"]()
    assert rc == 0
    assert json.loads(buf.getvalue())["decision"] == "allow"
