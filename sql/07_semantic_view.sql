-- Semantic view for Cortex Analyst — curated 360, not fragmented bronze tables

USE DATABASE AETHER_CARE;
USE SCHEMA GOLD;
USE WAREHOUSE AETHER_WH;

CREATE OR REPLACE SEMANTIC VIEW SV_MEMBER_360
  TABLES (
    members AS AETHER_CARE.GOLD.MEMBER_360
      PRIMARY KEY (MEMBER_ID)
      WITH SYNONYMS = ('member', 'patient', 'enrollee', 'beneficiary')
      COMMENT = 'Unified synthetic patient and member 360. One row per member.',
    factors AS AETHER_CARE.GOLD.ATRI_FACTORS
      PRIMARY KEY (MEMBER_ID, FACTOR_CODE, SOURCE_KEY)
      WITH SYNONYMS = ('risk factor', 'ATRI factor')
      COMMENT = 'Explainable ATRI points with source rows'
  )
  RELATIONSHIPS (
    factors (MEMBER_ID) REFERENCES members
  )
  FACTS (
    members.atri_score AS members.ATRI_SCORE
      COMMENT = 'Transparent ATRI points capped at 100. Not a black-box prediction.',
    members.age_years AS members.AGE_YEARS,
    members.active_med_count AS members.ACTIVE_MED_COUNT,
    members.ed_visits_90d AS members.ED_VISITS_90D,
    members.allowed_12m AS members.ALLOWED_12M,
    factors.points AS factors.POINTS
  )
  DIMENSIONS (
    members.member_id AS members.MEMBER_ID
      WITH SYNONYMS = ('member id', 'MEM id'),
    members.full_name AS members.FULL_NAME
      WITH SYNONYMS = ('name', 'patient name'),
    members.patient_id AS members.PATIENT_ID,
    members.atri_tier AS members.ATRI_TIER
      WITH SYNONYMS = ('risk tier', 'risk band'),
    members.panel AS members.PANEL,
    members.region AS members.REGION,
    members.line_of_business AS members.LINE_OF_BUSINESS
      WITH SYNONYMS = ('LOB', 'Medicare Advantage', 'commercial'),
    members.readmit_30d_flag AS members.READMIT_30D_FLAG
      WITH SYNONYMS = ('readmission', '30 day readmit'),
    members.open_gap_list AS members.OPEN_GAP_LIST
      WITH SYNONYMS = ('care gap', 'HEDIS gap', 'A1c gap'),
    members.safety_flag_list AS members.SAFETY_FLAG_LIST,
    members.active_condition_list AS members.ACTIVE_CONDITION_LIST,
    members.active_med_list AS members.ACTIVE_MED_LIST,
    factors.factor_code AS factors.FACTOR_CODE,
    factors.evidence AS factors.EVIDENCE
  )
  METRICS (
    members.member_count AS COUNT(members.MEMBER_ID)
      WITH SYNONYMS = ('how many members', 'panel size'),
    members.avg_atri AS AVG(members.ATRI_SCORE)
      COMMENT = 'Average ATRI on the filtered set',
    members.high_risk_count AS COUNT_IF(members.ATRI_TIER IN ('High', 'Very High'))
      WITH SYNONYMS = ('high risk count'),
    members.readmit_count AS COUNT_IF(members.READMIT_30D_FLAG)
  )
  COMMENT = 'Aether synthetic Member 360 for Cortex Analyst'
  AI_SQL_GENERATION 'Use MEMBER_360 for lists and scores. Join ATRI_FACTORS when asked why a member is high risk. Never invent medications. Data are synthetic.'
  AI_VERIFIED_QUERIES (
    very_high_atri AS (
      QUESTION 'How many Very High ATRI members are there?'
      SQL 'SELECT COUNT(*) AS N FROM AETHER_CARE.GOLD.MEMBER_360 WHERE ATRI_TIER = ''Very High'''
    ),
    hale_factors AS (
      QUESTION 'Why is MEM-10007 high risk? List ATRI factors.'
      SQL 'SELECT FACTOR_CODE, POINTS, SOURCE_OBJECT, SOURCE_KEY, EVIDENCE FROM AETHER_CARE.GOLD.ATRI_FACTORS WHERE MEMBER_ID = ''MEM-10007'' ORDER BY POINTS DESC'
    ),
    a1c_gaps AS (
      QUESTION 'Which members have an open A1c care gap?'
      SQL 'SELECT MEMBER_ID, EVIDENCE FROM AETHER_CARE.GOLD.CARE_GAPS WHERE MEASURE = ''GSD-A1c'''
    )
  );
