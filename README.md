# Aether 360 Copilot

Patient / Member 360 and a **cited** clinical–safety–regulatory document copilot for the Snowflake CoCo hackathon.

All people, claims, notes, and labels are **synthetic**. There is no production PHI.

Aether Care Alliance is a fictional regional IDN plus Medicare Advantage / commercial payer. Care managers, pharmacists, and UM nurses today bounce between EHR, claims, and PDFs. This solution joins those silos, publishes an explainable risk index, and answers questions only with retrieved evidence.

## What judges should see

| Criterion | Where it shows up |
| --- | --- |
| Real-world relevance | Care-manager 360, pharmacist DDI, UM prior-auth, quality A1c gaps |
| Technical execution | Dynamic Tables, Cortex Search ×2, Semantic View + verified queries, Cortex Agent, Streamlit |
| Completeness | Planning → SQL → app → eval questions → scheduled task |
| CoCo across the lifecycle | `coco/prompts/01`–`04`, project skills, plugin `aether-360` |
| Cited, not opaque | ATRI factor ledger; Q&A abstains without sources |
| Ingenuity | Reusable skills, MCP care-ops tickets, SQL guardrail hook, multi-agent handoff, nightly task |

**Hero member:** Jordan Hale `MEM-10007` — CHF, CKD3, T2DM, AFib, warfarin + ibuprofen, 30-day HF readmission, overdue A1c.

## Demo video

- Local file: [docs/demo/Aether360-demo.mp4](docs/demo/Aether360-demo.mp4) (1080p, ~2 min)
- After publishing to GitHub (see below), public URLs:
  - **Release (best for judges):** `https://github.com/<your-user>/aether-360-copilot/releases/download/v1.0.0/Aether360-demo.mp4`
  - **Raw in repo:** `https://raw.githubusercontent.com/<your-user>/aether-360-copilot/main/docs/demo/Aether360-demo.mp4`

Rebuild: `py -3.12 scripts/render_demo_video.py`

## Publish to public GitHub

```powershell
git remote add origin https://github.com/<your-user>/aether-360-copilot.git
git push -u origin main
```

Attach the demo MP4 to a GitHub release `v1.0.0` if judges should download it.

## Quick start (local, no Snowflake required)

```powershell
cd <this-repo-folder>
py -3.12 -m pip install -r requirements.txt
py -3.12 scripts/generate_synthetic.py
py -3.12 -m pytest tests -q
py -3.12 -m streamlit run app/streamlit_app.py
```

Open the **Cited copilot** tab and run the sample questions. Every answer shows source cards.

## CoCo lifecycle (required for judging)

In CoCo CLI (`cortex`) or Desktop, from this folder, paste the prompts in order:

1. Planning — `coco/prompts/01-planning.md`
2. Development — `coco/prompts/02-development.md` (creates `AETHER_CARE`, loads data, search, semantic view, agent)
3. Execution — `coco/prompts/03-execution.md` (task snapshot, agent chat, Streamlit)
4. Testing — `coco/prompts/04-testing.md`

Project skills (auto-loaded from `.cortex/skills/`):

- `$synthetic-care-data`
- `$patient-360-builder`
- `$cited-clinical-qa`
- `$risk-strat-explainer`
- `$aether-hackathon-lifecycle`

Shareable plugin: `.cortex-plugin/plugin.json` (`aether-360`). Slash command: `/aether360`.

## Architecture (short)

Siloed bronze EHR + claims + document stage → silver Dynamic Tables (conform, parse, chunk) → gold `MEMBER_360` + `ATRI_FACTORS` → Cortex Analyst semantic view + two Cortex Search services → Cortex Agent (router + tools) → Streamlit / CoWork / CoCo chat.

ATRI is a **published point system** (see `coco/planning/ontology.md`). Python (`aether360/risk.py`) is unit-tested; SQL (`sql/04_gold.sql`) mirrors it.

## Snowflake deploy order

`sql/00_setup.sql` → PUT CSVs and documents → `01` … `11`. Details in `sql/README.md`.

## MCP and guardrails

- `.mcp.json` — stdio server `mcp/care_ops_server.py` (`open_care_gap_ticket`, `post_safety_review`)
- `hooks/block_unsafe_sql.py` — blocks `DROP DATABASE` and SSN-shaped literals
- Agent refuses real-person lookups and off-topic scrape/hack requests

## Demo script

See `docs/DEMO.md`. Five minutes: population → Hale 360 → warfarin/NSAID question → SGLT2 safety → GLP-1 PA → abstain.
