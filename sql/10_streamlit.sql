-- Streamlit in Snowflake (after PUT of app + aether360 package to APP_STAGE)

USE DATABASE AETHER_CARE;
USE SCHEMA APP;
USE WAREHOUSE AETHER_WH;

-- From repo root (SnowSQL / CoCo):
-- PUT file://app/streamlit_app.py @AETHER_CARE.APP.APP_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- PUT file://aether360/*.py @AETHER_CARE.APP.APP_STAGE/aether360 AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

CREATE OR REPLACE STREAMLIT AETHER_360_COPILOT
  ROOT_LOCATION = '@AETHER_CARE.APP.APP_STAGE'
  MAIN_FILE = 'streamlit_app.py'
  QUERY_WAREHOUSE = AETHER_WH
  COMMENT = 'Aether Patient/Member 360 cited copilot (synthetic)';

-- Local fallback: streamlit run app/streamlit_app.py
