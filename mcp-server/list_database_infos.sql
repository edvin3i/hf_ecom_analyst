-- server/resources/sql/list_database_info.sql
-- Returns basic information about the current database in JSON format

SELECT jsonb_build_object(
    'database',
    jsonb_build_object(
        'name', current_database(),
        'description', (
            SELECT description
            FROM pg_shdescription
            JOIN pg_database ON pg_database.oid = pg_shdescription.objoid
            WHERE pg_database.datname = current_database()
            LIMIT 1
        )
    )
) AS database_info;
