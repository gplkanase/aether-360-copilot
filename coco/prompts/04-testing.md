# Phase 4 — Testing and validation (paste into CoCo)

Load `$cited-clinical-qa`. Fail the demo if any of these break.

1. Run `sql/11_validation.sql`. MEM-10007 must be Very High and include `DDI_WARF_NSAID` and `READMIT_30D`.
2. Run `pytest tests` from the repo root (local Python).
3. Ask the agent (or local copilot) the questions in `tests/eval_questions.yaml`.
   - Sourced answers must include object + key or doc chunk ids.
   - Real-person and scraper questions must refuse.
   - Unknown drug with no corpus hit must abstain.
4. Confirm SEARCH_PREVIEW returns warfarin NSAID language and Hale's ibuprofen note.
5. Confirm ATRI_SNAPSHOT has a row after the on-demand task.

If Analyst SQL is wrong, add a verified query rather than stuffing more synonyms.
