# Ontology — Aether Care clinical–payer language

This ontology is what Cortex Analyst and the agent must use. Synonyms are listed so natural language maps to one metric.

## Entities

| Entity | Meaning | Synonyms |
| --- | --- | --- |
| Member | Payer enrollee | patient, enrollee, beneficiary, person |
| Patient | EHR person | chart, clinic patient |
| Coverage | Plan product | MA, commercial, dual, plan |
| Encounter | EHR visit | admission, visit, stay |
| Claim | Payer billed event | medical claim, facility claim |
| Medication | Active drug | Rx, prescription, drug |
| Condition | Active diagnosis | ICD, problem, comorbidity |
| Document | Unstructured artifact | note, label, NCD, policy, alert |
| Care gap | Quality measure miss | HEDIS gap, star gap |
| ATRI | Transparent risk index | risk score, risk tier |

## Metrics (verified)

| Metric | Definition | Grain |
| --- | --- | --- |
| `member_count` | Count distinct `member_id` | query |
| `high_risk_count` | Members with `atri_tier` in (High, Very High) | query |
| `avg_atri` | Average `atri_score` | query |
| `readmit_30d_count` | Members with `readmit_30d_flag` = TRUE | query |
| `polypharmacy_count` | Members with `active_med_count` ≥ 5 | query |
| `open_gap_count` | Count of open rows in `CARE_GAPS` | query |
| `ed_90d_visits` | Sum of ED encounters in last 90 days | member or query |

## Dimensions

- `atri_tier`: Low | Moderate | High | Very High
- `line_of_business`: Medicare Advantage | Commercial | Dual
- `panel`: Heart Failure | Diabetes | General | COPD
- `region`: North Lake | River District | Summit County
- `document_class`: clinical_note | fda_label | cms_ncd | safety_alert | pa_policy | formulary | quality_spec

## ATRI factor catalog (codes used in GOLD.ATRI_FACTORS.factor_code)

| Code | Points | Evidence |
| --- | --- | --- |
| AGE_65_74 | 8 | member.dob |
| AGE_75_84 | 14 | member.dob |
| AGE_85P | 20 | member.dob |
| AGE_50_64 | 4 | member.dob |
| HCC_CHF | 18 | condition I50.* |
| HCC_CKD3P | 12 | condition N18.3–N18.6 |
| HCC_T2DM | 6 | condition E11.* |
| HCC_COPD | 10 | condition J44.* |
| HCC_AFIB | 8 | condition I48.* |
| HCC_CAD | 8 | condition I25.* |
| HCC_DEP | 5 | condition F32.* / F33.* |
| POLY_5_7 | 6 | active med count |
| POLY_8P | 12 | active med count |
| ED_90D | 8 each, cap 24 | encounters |
| READMIT_30D | 20 | encounters |
| GAP_A1C | 8 | last A1c > 6 months (diabetes) |
| GAP_PCP | 6 | no PCP 12 months |
| GAP_STATIN_CAD | 7 | CAD without statin |
| HIGH_COST | 10 | allowed ≥ 50000 in 12m |
| WARF_AGE75 | 9 | warfarin + age ≥ 75 |
| DDI_WARF_NSAID | 15 | warfarin + NSAID active |

Score is `LEAST(100, SUM(points))`. Tiers: 0–19 Low, 20–39 Moderate, 40–59 High, 60+ Very High.

## Document types (retrieval filters)

Use `document_class` as a Cortex Search attribute. Safety questions should filter `fda_label` OR `safety_alert` OR `clinical_note`. Coverage questions should filter `cms_ncd` OR `pa_policy` OR `formulary`.

## Verified example questions

1. How many Very High ATRI members are on the Heart Failure panel?
2. Why is MEM-10007 high risk? List factors and sources.
3. Which diabetics have an open glycemic-status care gap?
4. What does the synthetic Metforax label say about eGFR cutoffs?
5. Is ibuprofen listed as a bleeding risk with warfarin?
6. Summarize the CMS CGM coverage criteria and name members who might qualify.
