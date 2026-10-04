# Aether 360 — CoCo project instructions

You are Snowflake CoCo working in the **Aether Care Alliance** Patient/Member 360 and Clinical/Regulatory Document Copilot.

This repository is a CoCo-first hackathon solution. Prefer CoCo skills, SQL execution, and the prompts in `coco/prompts/` over hand-editing Snowflake objects.

## Non-negotiables

- Use **fully synthetic** data only. Never request, load, or generate real PHI, real member IDs, or production EHR/claims extracts.
- Every clinical, safety, or regulatory answer must include **cited evidence** (table + key, or document + chunk). If evidence is missing, **abstain**.
- Risk scores are **transparent rule-based** (Aether Transparent Risk Index). Never ship opaque model scores as the primary output.
- Do not invent medications, diagnoses, coverage decisions, or FDA/CMS text. Retrieve them.

## Warehouse layout

| Layer | Schema | Purpose |
| --- | --- | --- |
| Setup | `AETHER_CARE.RAW` | Stages, bronze landing |
| Bronze | `AETHER_CARE.BRONZE` | Append-only siloed EHR, claims, documents |
| Silver | `AETHER_CARE.SILVER` | Dynamic Tables: conformed, parsed, chunked |
| Gold | `AETHER_CARE.GOLD` | Member 360, ATRI factors, semantic view |
| Agents | `AETHER_CARE.AGENTS` | Cortex Search, Agent, procedures |
| App | `AETHER_CARE.APP` | Streamlit |

Warehouse: `AETHER_WH`. Database: `AETHER_CARE`.

## Skills to load

Project skills live in `.cortex/skills/`. Invoke them by name:

- `$synthetic-care-data` — generate referentially consistent synthetic datasets
- `$patient-360-builder` — bronze→silver→gold 360 + ATRI
- `$cited-clinical-qa` — retrieval + citation + abstain contract
- `$risk-strat-explainer` — transparent factor scoring
- `$aether-hackathon-lifecycle` — planning → build → run → test loop

## Build order

1. Run prompts in `coco/prompts/01-planning.md` (do not skip).
2. Generate or load synthetic data (`python -m scripts.generate_synthetic` locally, or the CoCo prompt in `02-development.md`).
3. Apply SQL in `sql/` in numeric order.
4. Deploy the Cortex Agent and Streamlit app.
5. Execute `coco/prompts/04-testing.md` and `tests/eval_questions.yaml`.

## Guardrails

- Out-of-scope (coding help, web scraping, real-patient lookup): refuse.
- Safety questions (drug–drug, boxed warnings): search regulatory + clinical notes, then cite both.
- Never reveal a raw score without the factor breakdown and source rows.
