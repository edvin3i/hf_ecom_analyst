-- BigQuery version: List all schemas (datasets) in the project
-- Returns a JSON object with schema information

SELECT TO_JSON_STRING(
  STRUCT(
    ARRAY(
      SELECT AS STRUCT
        schema_name as name,
        NULL as description  -- BigQuery doesn't have schema descriptions in INFORMATION_SCHEMA
      FROM INFORMATION_SCHEMA.SCHEMATA
      WHERE schema_name NOT IN ('INFORMATION_SCHEMA', 'information_schema')
      ORDER BY schema_name
    ) as schemas
  )
) as schema_list
