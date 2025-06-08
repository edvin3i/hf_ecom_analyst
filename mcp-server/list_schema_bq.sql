-- BigQuery version: List all datasets in the nodal-pod-462214-f0 project
-- Using region-qualified INFORMATION_SCHEMA for SCHEMATA


SELECT
  TO_JSON_STRING(ARRAY(
      SELECT
        STRUCT('huggingface_1' AS name, 'Dataset for e-commerce project' AS description)
    )) as schemas;

