import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from mcp.server.fastmcp import FastMCP
from pathlib import Path

# Load environment variables
load_dotenv()

LIST_SCHEMA=os.getenv('LIST_SCHEMA')
LIST_DATABASE_INFOS=os.getenv('LIST_DATABASE_INFOS')
TABLE_IN_SCHEMA=os.getenv('TABLE_IN_SCHEMA')
COLUMN_IN_TABLE=os.getenv('COLUMN_IN_TABLE')
VIEWS_SQL_FILE = os.getenv('VIEWS_SQL_FILE')


class DatabaseInterface:
    def __init__(self):
        # Initialize FastMCP server
        self.mcp = FastMCP("ecommerce-mcp-server")
        
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        print('=============>',self.db_config)
        
    def get_db_connection(self):
        """Create database connection"""
        return psycopg2.connect(**self.db_config)

    def list_schemas(self):
        print("=======>", LIST_SCHEMA)
        sql_path = Path(LIST_SCHEMA)
        with sql_path.open("r", encoding="utf-8") as f:
            query = f.read()

        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchone()[0]  # JSON object
                return result
        finally:
            conn.close()

    def list_database_info(self):
        sql_path = Path(LIST_DATABASE_INFOS)
        with sql_path.open("r", encoding="utf-8") as f:
            query = f.read()

        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchone()[0]  # JSON object
                return result
        finally:
            conn.close()
    
    def list_tables_in_schema(self, schema_name: str):
        sql_path = Path(TABLE_IN_SCHEMA)
        with sql_path.open("r", encoding="utf-8") as f:
            query = f.read()

        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, {'schema_name': schema_name})
                result = cur.fetchone()[0]  # JSON object
                return result
        finally:
            conn.close()
    
    def list_columns_in_table(self, schema_name: str, table_name: str):
        sql_path = Path(COLUMN_IN_TABLE)
        with sql_path.open("r", encoding="utf-8") as f:
            query = f.read()

        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, {
                    'schema_name': schema_name,
                    'table_name': table_name
                })
                result = cur.fetchone()[0]  # JSON object
                return result
        finally:
            conn.close()
    
    def create_view(self, view_name: str, query: str, validate_only: bool = False):
        """Create or replace a SQL view with proper error handling and validation"""
        # Input validation
        if not view_name or not view_name.strip():
            return "❌ View name cannot be empty"
        if not query or not query.strip():
            return "❌ Query cannot be empty"
        # Sanitize view name (basic validation)
        if not view_name.replace('_', '').replace('-', '').isalnum():
            return "❌ View name contains invalid characters. Use only letters, numbers, underscores, and hyphens"
        if validate_only:
        # Just validate the query without executing
            try:
                conn = self.get_db_connection()
                with conn.cursor() as cur:
                    cur.execute(f"EXPLAIN {query}")
                    return f"✅ Query is valid for view '{view_name}'"
            except Exception as e:
                return f"❌ Invalid query: {str(e)}"
            finally:
                conn.close()
        try:
            conn = self.get_db_connection()
            try:
                with conn.cursor() as cur:
                    # Drop view with CASCADE to handle dependencies
                    drop_view_query = f"DROP VIEW IF EXISTS {view_name} CASCADE"
                    cur.execute(drop_view_query)
                    
                    # Create the new view
                    create_view_query = f"CREATE VIEW {view_name} AS {query}"
                    cur.execute(create_view_query)
                    
                    # Commit the transaction
                    conn.commit()
                    return f"✅ View '{view_name}' created successfully"
                    
            except psycopg2.Error as db_error:
                # Rollback on database errors
                conn.rollback()
                return f"❌ Database error creating view '{view_name}': {str(db_error)}"
            except Exception as e:
                # Rollback on any other errors
                conn.rollback()
                return f"❌ Error creating view '{view_name}': {str(e)}"
            finally:
                conn.close()
                
        except Exception as connection_error:
            return f"❌ Connection error: {str(connection_error)}"

    def list_views_detailed(self):
        """List all views with metadata"""
        query = """
        SELECT 
            schemaname,
            viewname,
            viewowner,
            definition
        FROM pg_views 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, viewname
        """
        return self.read_only_query(query)

    def get_view_content(self, view_name: str, limit: int = 100):
        """Get sample content from a view"""
        try:
            query = f"SELECT * FROM {view_name} LIMIT {limit}"
            return self.read_only_query(query)
        except Exception as e:
            return f"❌ Error querying view: {str(e)}"

    def drop_view(self, view_name: str):
        """Drop a specific view"""
        if not view_name or not view_name.strip():
            return "❌ View name cannot be empty"
        
        try:
            conn = self.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE")
                    conn.commit()
                    return f"✅ View '{view_name}' dropped successfully"
            except Exception as e:
                conn.rollback()
                return f"❌ Error dropping view: {str(e)}"
            finally:
                conn.close()
        except Exception as e:
            return f"❌ Connection error: {str(e)}"

    def execute_sql_file(self, file_path: str):
        """Execute SQL statements from a file"""
        sql_path = Path(file_path)
        if not sql_path.exists():
            return f"❌ SQL file not found: {file_path}"
        
        try:
            with sql_path.open("r", encoding="utf-8") as f:
                sql_content = f.read()
            conn = self.get_db_connection()
            try:
                with conn.cursor() as cur:
                    # Split SQL content by semicolon and execute each statement
                    sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
                    executed_commands = []
                    for command in sql_commands:
                        if command:  # Skip empty commands
                            cur.execute(command)
                            executed_commands.append(command.split()[0:3])  # First few words for logging
                    
                    conn.commit()
                    return f"✅ Successfully executed {len(executed_commands)} SQL commands"
                    
            except Exception as e:
                conn.rollback()
                return f"❌ Error executing SQL file: {str(e)}"
            finally:
                conn.close()
                
        except Exception as e:
            return f"❌ Error reading SQL file: {str(e)}"
    
    def create_analytics_views(self):
        """Create all analytics views from SQL file"""
        print("=============>", VIEWS_SQL_FILE)
        if not VIEWS_SQL_FILE:
            return "❌ VIEWS_SQL_FILE environment variable not set"
        return self.execute_sql_file(VIEWS_SQL_FILE)

    def read_only_query(self, query):
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(query)
                result = cur.fetchall()  # JSON object
                return result
        finally:
            conn.close()

    def create_temp_table_from_query(self, table_name: str, source_query: str) -> str:
        """Create temporary table from any SELECT query"""
        try:
            conn = self.get_db_connection()
            try:
                with conn.cursor() as cur:
                    temp_query = f"CREATE TEMP TABLE {table_name} AS {source_query}"
                    cur.execute(temp_query)
                    conn.commit()
                    print(f"✅ Temporary table '{table_name}' created successfully")
                    return f"✅ Temporary table '{table_name}' created successfully"
            except Exception as e:
                conn.rollback()
                return f"❌ Error creating temp table: {str(e)}"
            finally:
                conn.close()
        except Exception as e:
            return f"❌ Connection error: {str(e)}"
