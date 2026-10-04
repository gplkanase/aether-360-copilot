# Five-minute demo

Watch the packaged walkthrough first: [Aether360-demo.mp4](demo/Aether360-demo.mp4) (~2 min, captions on).

All records are synthetic. Say that out loud.

## 1. CoCo planning evidence (30s)

Show `coco/planning/ontology.md` and that CoCo was given `coco/prompts/01-planning.md` before DDL.

## 2. Population (45s)

Streamlit **Population** tab.

- 36 members, ATRI mix, 30-day readmit count.
- Sort implicitly by ATRI: Jordan Hale is Very High.

## 3. Member 360 (60s)

Sidebar → `MEM-10007 — Jordan Hale`.

- Point at the **factor ledger**: readmission, CHF, CKD, polypharmacy, warfarin+age, warfarin+NSAID, A1c gap.
- Emphasize: this is not an ML score. Each row has a source table and key.

## 4. Cited copilot (2 min)

Sample questions:

1. *Is ibuprofen safe given MEM-10007's anticoagulant?*  
   Expect med list + PCP/pharmacy note + synthetic warfarin label NSAID language.
2. *River Chen is on an SGLT2 — what does the safety communication require?*  
   Expect hold-during-vomiting language + ED note ketones.
3. *Does Ellis Navarro meet PA-GLP1-2026 diabetes criteria?*  
   Expect policy chunks + A1c 8.1 + metformin.
4. *What is Elon Musk's A1c in production EHR?*  
   Expect refuse.

## 5. CoCo execution (45s)

If connected: `EXECUTE TASK AETHER_CARE.GOLD.ATRI_NIGHTLY_REFRESH` and chat `AETHER_360_AGENT` with question 1.

Optional: MCP `open_care_gap_ticket` for Hale's DDI.

## Talking points if asked

- Why one gold 360 table? Cortex Analyst accuracy on fragmented EHR+claims joins is poor; we materialize the analytical surface first (domain skill `$patient-360-builder`).
- Why two search services? Clinical notes vs  policy/labels so filters and citations stay clean.
- Why abstain? Safety and coverage language must not be hallucinated.
