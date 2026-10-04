-- Cortex Agent: structured 360 + dual document search + action tools

USE DATABASE AETHER_CARE;
USE SCHEMA AGENTS;
USE WAREHOUSE AETHER_WH;

CREATE OR REPLACE AGENT AETHER_360_AGENT
  COMMENT = 'Synthetic Patient/Member 360 and cited clinical-regulatory copilot'
  PROFILE = '{"display_name": "Aether 360 Copilot", "color": "teal"}'
  FROM SPECIFICATION
$$
models:
  orchestration: auto

orchestration:
  capabilities:
    analytical_search: true
  tool_not_accessible: accept
  budget:
    seconds: 45
    tokens: 24000

instructions:
  response: |
    You are the Aether Care Alliance copilot. All data are fully synthetic.
    Every factual sentence must cite a source (semantic view row, GET_MEMBER_360 factor, or Cortex Search chunk).
    ATRI is a transparent rules index, never a mortality or cost prediction.
    If retrieval is empty, abstain. Never invent ICD codes, doses, or coverage rules.
    Prefer quotes for label/NCD/policy language. Do not make coverage more permissive than the snippet.
  orchestration: |
    Route metrics, lists, counts, and ATRI to Analyst (SV_MEMBER_360).
    Route "why is this member high risk" to GET_MEMBER_360 plus Analyst factors.
    Route notes to SEARCH_CLINICAL. Route labels, NCD, PA, formulary, safety alerts to SEARCH_REGULATORY.
    Mixed safety questions (warfarin+NSAID, SGLT2 ketosis, GLP-1 PA) call both structured tools and search, then merge.
    Refuse real-person PHI lookups and off-topic coding/scraping requests.
    After a confirmed care-gap action request, call OPEN_CARE_GAP_TICKET.
  sample_questions:
    - question: Why is MEM-10007 high risk? List ATRI factors and sources.
    - question: Is ibuprofen safe given Jordan Hale's anticoagulant?
    - question: Which members have an open A1c care gap?
    - question: What does the synthetic CMS CGM coverage criteria require?

tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: Member360Analyst
      description: Text-to-SQL over the curated synthetic Member 360 semantic view and ATRI factors.
  - tool_spec:
      type: cortex_search
      name: ClinicalNotesSearch
      description: Hybrid search over synthetic clinical notes (discharge, PCP, ED, pharmacy).
  - tool_spec:
      type: cortex_search
      name: RegulatorySearch
      description: Hybrid search over synthetic FDA-style labels, CMS NCD, PA policy, formulary, safety alerts.
  - tool_spec:
      type: generic
      name: GetMember360
      description: Return the Member 360 object and ATRI factor ledger for one synthetic member_id.
      input_schema:
        type: object
        properties:
          MEMBER_ID:
            type: string
            description: Synthetic member id such as MEM-10007
        required: [MEMBER_ID]
  - tool_spec:
      type: generic
      name: OpenCareGapTicket
      description: Open a synthetic care-management ticket. Not a real Jira instance.
      input_schema:
        type: object
        properties:
          MEMBER_ID:
            type: string
          REASON:
            type: string
          OWNER:
            type: string
        required: [MEMBER_ID, REASON]

tool_resources:
  Member360Analyst:
    semantic_view: AETHER_CARE.GOLD.SV_MEMBER_360
  ClinicalNotesSearch:
    search_service: AETHER_CARE.AGENTS.SEARCH_CLINICAL
    max_results: "6"
    title_column: TITLE
    id_column: CHUNK_ID
  RegulatorySearch:
    search_service: AETHER_CARE.AGENTS.SEARCH_REGULATORY
    max_results: "6"
    title_column: TITLE
    id_column: CHUNK_ID
  GetMember360:
    type: function
    execution_environment:
      type: warehouse
      warehouse: AETHER_WH
    identifier: AETHER_CARE.AGENTS.GET_MEMBER_360
  OpenCareGapTicket:
    type: function
    execution_environment:
      type: warehouse
      warehouse: AETHER_WH
    identifier: AETHER_CARE.AGENTS.OPEN_CARE_GAP_TICKET
$$;
