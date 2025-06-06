-- server/resources/sql/list_tables_in_schema.sql
-- Returns all user-defined tables in a given schema with their descriptions as JSON
-- Uses a parameter :schema_name

WITH tables AS (
    SELECT
        table_name,
        obj_description(('"' || table_schema || '"."' || table_name || '"')::regclass) AS description
    FROM information_schema.tables
    WHERE table_schema = %(schema_name)s
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
)
SELECT jsonb_build_object(
    'tables',
    jsonb_agg(
        jsonb_build_object(
            'name', table_name,
            'description', description
        )
    )
) AS table_list
FROM tables;
