# SQL apply order

Run on warehouse `AETHER_WH` after `python scripts/generate_synthetic.py`.

From the repo root, PUT files (SnowSQL or CoCo):

```
PUT file://data/generated/*.csv @AETHER_CARE.RAW.CSV_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://data/documents/* @AETHER_CARE.RAW.DOCS_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
ALTER STAGE AETHER_CARE.RAW.DOCS_STAGE REFRESH;
```

Then:

| File | Purpose |
| --- | --- |
| `00_setup.sql` | DB, warehouse, stages |
| `01_bronze.sql` | Landing tables + COPY INTO |
| `02_silver.sql` | Dynamic Tables for conformed EHR/claims |
| `03_parse_documents.sql` | Parse + chunk |
| `04_gold.sql` | MEMBER_360 + ATRI_FACTORS |
| `05_cortex_search.sql` | Clinical + regulatory search |
| `06_procedures.sql` | GET_MEMBER_360, OPEN_CARE_GAP_TICKET |
| `07_semantic_view.sql` | Cortex Analyst |
| `08_agent.sql` | Cortex Agent |
| `09_tasks.sql` | Nightly ATRI snapshot |
| `10_streamlit.sql` | Streamlit in Snowflake |
| `11_validation.sql` | Judge/test queries |

If a DDL dialect differs in your account (semantic view verified queries, agent spec), use the CoCo `semantic-view` and `cortex-agent` skills with the comments in those files as the spec — do not weaken the citation contract.
