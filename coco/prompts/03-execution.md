# Phase 3 — Execution (paste into CoCo)

Run the end-to-end path, including an unattended task.

1. Refresh silver/gold Dynamic Tables if they are still initializing.
2. `EXECUTE TASK AETHER_CARE.GOLD.ATRI_NIGHTLY_REFRESH;` then `SELECT * FROM AETHER_CARE.GOLD.ATRI_SNAPSHOT LIMIT 20;`
3. Optionally `ALTER TASK AETHER_CARE.GOLD.ATRI_NIGHTLY_REFRESH RESUME;` for scheduled 06:00 UTC runs.
4. Chat with agent `AETHER_CARE.AGENTS.AETHER_360_AGENT`:
   - Why is MEM-10007 high risk? List ATRI factors and sources.
   - Is ibuprofen safe given Jordan Hale's anticoagulant?
   - Which members have an open A1c care gap?
5. Deploy Streamlit from `sql/10_streamlit.sql` (or run `streamlit run app/streamlit_app.py` locally).
6. If MCP `aether-care-ops` is configured, open a ticket for MEM-10007 warfarin+NSAID review.

Show me the SQL results and the agent answers with citations.
