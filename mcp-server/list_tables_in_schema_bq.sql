-- BigQuery version: Returns all tables in the specified dataset
-- Using dataset-qualified INFORMATION_SCHEMA for TABLES

SELECT TO_JSON_STRING(
  STRUCT(
    ARRAY(
      SELECT AS STRUCT
        table_name as name,
        NULL as description
      FROM `nodal-pod-462214-f0.huggingface_1.INFORMATION_SCHEMA.TABLES`
      WHERE table_schema = %(schema_name)s
        AND table_type = 'BASE TABLE'
      ORDER BY table_name
    ) as tables
  )
) as table_list
