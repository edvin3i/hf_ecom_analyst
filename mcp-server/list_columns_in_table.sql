-- server/resources/sql/list_columns_in_table.sql
-- Returns column metadata for a specific table as a JSON object
-- Uses parameters: :schema_name, :table_name

WITH columns AS (
    SELECT
        cols.column_name,
        cols.data_type,
        col_description(('"' || cols.table_schema || '"."' || cols.table_name || '"')::regclass, cols.ordinal_position) AS description
    FROM information_schema.columns cols
    WHERE cols.table_schema = %(schema_name)s
      AND cols.table_name = %(table_name)s
    ORDER BY cols.ordinal_position
)
SELECT jsonb_build_object(
    'columns',
    jsonb_agg(
        jsonb_build_object(
            'name', column_name,
            'type', data_type,
            'description', description
        )
    )
) AS column_list
FROM columns;
