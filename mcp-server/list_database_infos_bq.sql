-- BigQuery version: Returns basic information about the current project

SELECT TO_JSON_STRING(
  STRUCT(
    STRUCT(
      @@project_id as name,
      'BigQuery project dataset' as description
    ) as database
  )
) as database_info
