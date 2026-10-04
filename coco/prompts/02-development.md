# Phase 2 — Development (paste into CoCo after planning)

Load `$synthetic-care-data`, `$patient-360-builder`, `$cited-clinical-qa`, and `$risk-strat-explainer`.

Work in this repo. Prefer executing the SQL files over rewriting them unless a Snowflake error forces a fix.

1. Run locally (or generate in Snowflake if you prefer):

```text
python scripts/generate_synthetic.py
```

2. Execute `sql/00_setup.sql` then PUT:
   - `data/generated/*.csv` → `@AETHER_CARE.RAW.CSV_STAGE`
   - `data/documents/*` → `@AETHER_CARE.RAW.DOCS_STAGE`
3. Execute `sql/01_bronze.sql` through `sql/09_tasks.sql` in order.
4. If `CREATE SEMANTIC VIEW` asks for interactive options, keep names `SV_MEMBER_360` and verified queries already in `sql/07_semantic_view.sql`.
5. Create the agent from `sql/08_agent.sql` (or `/cortex-agent` with those tools and the orchestration text).
6. Do not skip citation instructions in the agent spec.

When objects exist, print row counts for MEMBER_360, ATRI_FACTORS, DOC_CHUNKS.
