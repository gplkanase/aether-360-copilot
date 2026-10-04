# Data model

Database `AETHER_CARE`. All keys are synthetic (`MEM-*`, `PAT-*`, `DOC-*`).

## Identity

Two source systems, one person:

| Source | Natural key | Gold key |
| --- | --- | --- |
| Payer (claims) | `MEMBER_ID` | `MEMBER_ID` |
| EHR | `PATIENT_ID` | joined via `MEMBER_PATIENT_XWALK` |

`GOLD.MEMBER_360.member_id` is the copilot’s primary identifier. `patient_id` is always shown when joined.

## Bronze (siloed)

```
BRONZE.EHR_PATIENTS          -- demographics as the clinic sees them
BRONZE.EHR_ENCOUNTERS
BRONZE.EHR_CONDITIONS
BRONZE.EHR_MEDICATIONS
BRONZE.EHR_LABS
BRONZE.EHR_NOTES_RAW         -- note metadata; body on stage
BRONZE.PAYER_MEMBERS
BRONZE.PAYER_COVERAGE
BRONZE.PAYER_MEDICAL_CLAIMS
BRONZE.PAYER_PHARMACY_CLAIMS
BRONZE.DOC_MANIFEST          -- regulatory/legal file inventory
```

## Silver (Dynamic Tables, TARGET_LAG 5 minutes)

| Object | Grain | Notes |
| --- | --- | --- |
| `SILVER.PERSON_XWALK` | member↔patient | Inner join only when both sides exist |
| `SILVER.ENCOUNTERS` | encounter | Visit type, LOS, unplanned flag |
| `SILVER.CONDITIONS_ACTIVE` | member × ICD-10 | End-dated rows excluded |
| `SILVER.MEDICATIONS_ACTIVE` | member × Rx | Includes drug class |
| `SILVER.LABS` | lab result | Numeric value + units |
| `SILVER.CLAIMS` | claim line | Allowed amount, POS |
| `SILVER.PARSED_DOCUMENTS` | document | `AI_PARSE_DOCUMENT` LAYOUT |
| `SILVER.DOC_CHUNKS` | chunk | `SPLIT_TEXT_RECURSIVE_CHARACTER` 1800/300 |

## Gold

| Object | Grain | Purpose |
| --- | --- | --- |
| `GOLD.MEMBER_360` | member | Denormalized profile for Analyst + UI |
| `GOLD.ATRI_FACTORS` | member × factor | Points, rule id, source row |
| `GOLD.CARE_GAPS` | member × measure | HEDIS-like gaps with evidence |
| `GOLD.SAFETY_FLAGS` | member × flag | Drug–drug, boxed-warning match |

`MEMBER_360` is **curated for text-to-SQL** (lesson: do not expose 20 fragmented tables to Analyst). Medications, conditions, and gap lists are pre-aggregated as strings **and** kept in child tables for citation.

## Streams and tasks

- Stream on `SILVER.DOC_CHUNKS` → Cortex Search incremental-friendly lag 1 hour.
- Task `ATRI_NIGHTLY_REFRESH` `USING CRON '0 6 * * * UTC'` inserts into `GOLD.ATRI_SNAPSHOT`.

## Referential rules (synthetic generator must honor)

- Every `PATIENT_ID` in EHR tables exists in `EHR_PATIENTS`.
- Every `MEMBER_ID` in claims tables exists in `PAYER_MEMBERS`.
- Every hero member has ≥1 note and ≥1 claim.
- Medication NDC/name used in notes appears in `EHR_MEDICATIONS` or pharmacy claims.
- Lab `A1C` rows exist for all members with diabetes (even if overdue).
