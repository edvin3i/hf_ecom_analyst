-- BigQuery version: Returns column metadata for a specific table
-- Parameters %(schema_name)s and %(table_name)s will be replaced programmatically

SELECT TO_JSON_STRING(
  STRUCT(
    ARRAY(
      SELECT AS STRUCT
        column_name as name,
        data_type as type,
        NULL as description  -- BigQuery INFORMATION_SCHEMA doesn't include column descriptions
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE table_schema = %(schema_name)s
        AND table_name = %(table_name)s
      ORDER BY ordinal_position
    ) as columns
  )
) as column_list
