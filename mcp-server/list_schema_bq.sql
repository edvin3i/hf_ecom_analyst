-- BigQuery version: List all datasets in the nodal-pod-462214-f0 project
-- Using region-qualified INFORMATION_SCHEMA for SCHEMATA

SELECT TO_JSON_STRING(
  STRUCT(
    ARRAY(
      SELECT AS STRUCT
        schema_name as name,
        NULL as description
      FROM `region-europe-west1.INFORMATION_SCHEMA.SCHEMATA`
      WHERE catalog_name = 'nodal-pod-462214-f0'
        AND schema_name NOT IN ('INFORMATION_SCHEMA', 'information_schema')
      ORDER BY schema_name
    ) as schemas
  )
) as schema_list
