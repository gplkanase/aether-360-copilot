# Solution design

## Architecture

```
EHR silo (bronze)     Claims silo (bronze)     Document stage (bronze)
   patients               members                  PDF/MD files
   encounters             coverage                 clinical notes
   conditions             medical claims
   meds / labs            pharmacy claims
            \                 |                  /
             \                |                 /
              v               v                v
           SILVER Dynamic Tables (conform + parse + chunk)
                          |
                          v
              GOLD MEMBER_360 + ATRI_FACTORS
                          |
          +---------------+----------------+
          |               |                |
   Semantic View    Cortex Search     Procedures
   (Analyst)        clinical+reg      GET_360 / OPEN_TICKET
          |               |                |
          +---------------+----------------+
                          |
                   Cortex Agent (router)
                          |
              Streamlit  |  CoCo chat  |  CoWork
                          |
                    MCP care-ops tickets
```

## CoCo surfaces (judging)

| Phase | Where CoCo is used |
| --- | --- |
| Planning | Catalog exploration prompts, this design, ontology, data model |
| Development | Skills generate SQL, semantic view, search, agent, Streamlit |
| Execution | Dynamic Table refresh, task `ATRI_NIGHTLY_REFRESH`, agent chat |
| Testing | Eval question set, citation checks, abstain tests |

## Multi-agent orchestration

| Agent | Job | Tools |
| --- | --- | --- |
| Router | Classify 360 vs clinical vs regulatory vs mixed vs refuse | none |
| Structured 360 | Metrics, lists, care gaps, ATRI | Cortex Analyst + GET_MEMBER_360 |
| Document evidence | Notes, labels, NCD, PA policy | Cortex Search (two services) |
| Safety/regulatory | Drug–drug, boxed warning, coverage | Search + Analyst |
| Citation guardrail | Reject answers without sources; downgrade confidence | validate_citations UDF |

Handoff rule: the router never answers from memory. It always calls a specialist. The guardrail runs last.

## Evidence contract

Every assistant message must include a `sources[]` array:

```json
{
  "claim": "Member is on warfarin 5 mg daily",
  "source_type": "structured",
  "object": "GOLD.MEMBER_MEDICATIONS",
  "key": "MEM-10007 / Rx-4412",
  "snippet": "warfarin 5 mg PO daily, start 2024-11-02"
}
```

or

```json
{
  "claim": "NSAIDs increase bleeding risk with warfarin",
  "source_type": "document",
  "object": "DOC-FDA-WARFARIN",
  "key": "chunk-12",
  "snippet": "Avoid concomitant NSAIDs unless benefit outweighs bleeding risk."
}
```

If `sources` is empty → response_type = `abstain`.

## Ingenuity (CoCo extras)

- **Reusable plugin** `aether-360` with four domain skills.
- **Custom generic tools** on the Cortex Agent (360 lookup, ticket open).
- **MCP care-ops server** for tickets (Jira-shaped, local/synthetic).
- **Scheduled Task** for ATRI snapshot history.
- **PreToolUse hook** blocking DROP/production-like identifiers.
- Same solution runnable in **CoCo CLI**, Desktop (project skills), and Streamlit.
