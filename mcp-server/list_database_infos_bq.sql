-- BigQuery version: Returns information about the nodal-pod-462214-f0 project

SELECT TO_JSON_STRING(
  STRUCT(
    STRUCT(
      'nodal-pod-462214-f0' as name,
      'BigQuery project for Hugging Face e-commerce data' as description
    ) as database
  )
) as database_info
