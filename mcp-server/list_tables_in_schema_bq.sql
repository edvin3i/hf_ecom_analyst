-- BigQuery version: Returns all tables in a given schema (dataset)
-- Parameter %(schema_name)s will be replaced programmatically

SELECT TO_JSON_STRING(
  STRUCT(
    ARRAY(
      SELECT AS STRUCT
        table_name as name,
        NULL as description  -- BigQuery doesn't store table descriptions in INFORMATION_SCHEMA
      FROM INFORMATION_SCHEMA.TABLES
      WHERE table_schema = %(schema_name)s
        AND table_type = 'BASE TABLE'
      ORDER BY table_name
    ) as tables
  )
) as table_list
