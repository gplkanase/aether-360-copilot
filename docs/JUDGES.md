# Judge map — challenge bullets → this repo

| Challenge ask | Implementation |
| --- | --- |
| Unify EHR + claims + documents | Bronze silos, `MEMBER_PATIENT_XWALK`, gold `MEMBER_360` |
| Synthetic / de-identified only | `scripts/generate_synthetic.py`, `MEM-*` / `PAT-*`, refuse real-person prompts |
| Risk stratification with evidence | ATRI factor ledger (`aether360/risk.py`, `sql/04_gold.sql`) |
| Cited Q&A, never opaque predictions | `aether360/qa.py`, Cortex Agent instructions, abstain path |
| CoCo planning | `coco/planning/*`, `coco/prompts/01-planning.md` |
| CoCo development | skills + `sql/00`–`08`, `coco/prompts/02-development.md` |
| CoCo execution | Task, agent chat, Streamlit, `coco/prompts/03-execution.md` |
| CoCo testing | `sql/11_validation.sql`, `pytest tests`, `coco/prompts/04-testing.md` |
| Reusable skills (headline bonus) | `.cortex/skills/*`, plugin `aether-360` |
| MCP | `.mcp.json` + `mcp/care_ops_server.py` |
| Automations | `ATRI_NIGHTLY_REFRESH` cron |
| Custom tools | `GET_MEMBER_360`, `OPEN_CARE_GAP_TICKET` |
| Multi-agent | `.cortex/agents/*` + Cortex Agent routing |
| Guardrails | citation contract, hook, refuse/abstain |
| Streamlit | `app/streamlit_app.py` |
| Unstructured | parse + chunk + dual Cortex Search |
| Semantic / ontology | `coco/planning/ontology.md`, `sql/07_semantic_view.sql` |
