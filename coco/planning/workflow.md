# Workflow — from question to cited answer

```
User question
    │
    ├─ Guardrail: refuse real-PHI, off-topic, criminal, or “just predict”
    │
    ├─ Router
    │     ├─ member/metrics/gaps/ATRI     → Structured 360 agent
    │     ├─ note/label/NCD/policy        → Document evidence agent
    │     ├─ interaction / mixed          → both, then merge
    │     └─ unknown                      → abstain + ask for member id or doc class
    │
    ├─ Retrieve
    │     ├─ Analyst SQL against SV_MEMBER_360 (verified queries preferred)
    │     ├─ GET_MEMBER_360(member_id) procedure
    │     └─ Cortex Search (clinical index + regulatory index)
    │
    ├─ Score / flags (always rule-based)
    │     └─ ATRI_FACTORS + SAFETY_FLAGS
    │
    ├─ Citation guardrail
    │     ├─ every factual sentence has a source
    │     ├─ snippets quoted, not paraphrased away
    │     └─ fail → abstain
    │
    └─ Optional action
          └─ MCP open_care_gap_ticket / OPEN_CARE_GAP_TICKET procedure
```

## Care-manager happy path (demo)

1. Population view: High / Very High ATRI, sorted.
2. Open **Jordan Hale (MEM-10007)**.
3. Read factor list (readmission, CHF, CKD, polypharmacy, warfarin-age, NSAID DDI).
4. Ask: *Is ibuprofen safe given this member’s anticoagulant?*
5. Copilot cites med row + visit note + synthetic warfarin label.
6. Optional: open a pharmacist review ticket via MCP.

## Nightly unattended path

Task `ATRI_NIGHTLY_REFRESH` writes `GOLD.ATRI_SNAPSHOT`. Streamlit and Analyst read the latest snapshot date. This is the scheduled-run story for judges.
