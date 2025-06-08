-- BigQuery version: Returns column metadata for tables in the huggingface_1 dataset
-- Using dataset-qualified INFORMATION_SCHEMA for COLUMNS

SELECT TO_JSON_STRING(
  STRUCT(
    ARRAY(
      SELECT AS STRUCT
        column_name as name,
        data_type as type,
        NULL as description
      FROM `nodal-pod-462214-f0.huggingface_1.INFORMATION_SCHEMA.COLUMNS`
      WHERE table_schema = %(schema_name)s
        AND table_name = %(table_name)s
      ORDER BY ordinal_position
    ) as columns
  )
) as column_list
