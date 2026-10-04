# Problem framing — Aether Care Alliance

**Fictional organization.** Aether Care Alliance is a regional integrated delivery network plus Medicare Advantage / commercial payer. All people, claims, notes, labels, and policies in this project are synthetic.

## Who is blocked today

| Role | Silo they live in | Question they cannot answer quickly |
| --- | --- | --- |
| Care manager | Claims + care-gap worklists | Why is this member high risk, and what evidence should I act on? |
| Clinical pharmacist | EHR meds + FDA labels | Is this combination contraindicated, and where is that written? |
| Utilization / PA nurse | Policy PDFs + claims | Does this GLP-1 request meet the 2026 coverage rule? |
| Regulatory / safety | Safety alerts + notes | Who is on an SGLT2 and has a ketosis-risk note? |
| Quality lead | HEDIS specs + labs | Which diabetics are overdue for A1c, with source labs? |

## Failure mode we will not ship

Opaque “AI risk 0.81” with no factors, no rows, and no document snippets. Judges and clinicians cannot audit that.

## Outcome

A copilot that:

1. Joins EHR patient records to payer member records (crosswalk).
2. Publishes a **Member 360** gold record plus an **explainable** ATRI score.
3. Parses unstructured clinical, formulary, CMS, and synthetic-label documents.
4. Answers in a Q&A UI with **inline citations** and an abstain path.

## Success tests (planning-phase)

- A care manager can open Jordan Hale and see every ATRI factor with a source table.
- “Is ibuprofen safe with Jordan Hale’s anticoagulant?” returns cited label + note + med row — or abstains.
- “Which members need a CGM coverage review?” retrieves CMS NCD chunks plus structured diabetes flags.
- Asking for a real person’s record is refused.
