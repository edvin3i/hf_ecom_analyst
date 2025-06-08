import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import requests
import json
from mcp.server.fastmcp import FastMCP
from pathlib import Path

# Load environment variables
load_dotenv()

LIST_SCHEMA = os.getenv('LIST_SCHEMA_BQ')
LIST_DATABASE_INFOS = os.getenv('LIST_DATABASE_INFOS_BQ')
TABLE_IN_SCHEMA = os.getenv('TABLE_IN_SCHEMA_BQ')
COLUMN_IN_TABLE = os.getenv('COLUMN_IN_TABLE_BQ')
VIEWS_SQL_FILE = os.getenv('VIEWS_SQL_FILE_BQ')


class BigQueryInterface:
    def __init__(self):
        # Initialize FastMCP server
        self.mcp = FastMCP("bigquery-mcp-server")
        
        self.endpoint_url = os.getenv('BIGQUERY_ENDPOINT_URL')
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        # Only add authorization if API key is provided
        api_key = os.getenv('BIGQUERY_API_KEY')
        if api_key:
            self.headers['Authorization'] = f"Bearer {api_key}"
        
        if not self.endpoint_url:
            raise ValueError("BIGQUERY_ENDPOINT_URL environment variable is required")
        
        # Default project and dataset names
        self.project_name = "nodal-pod-462214-f0"
        self.dataset_name = "huggingface_1"
        
        print('=============> BigQuery endpoint:', self.endpoint_url)
        print(f'=============> Project: {self.project_name}, Dataset: {self.dataset_name}')
        print('=============> Available tables: articles, customers, transactions_train')

    def format_table_name(self, table_name: str) -> str:
        """
        Autocorrect table names to fully qualified format: project_name.dataset_name.table_name
        If the table name already has the project and/or dataset, leave it as is.
        """
        if not table_name:
            return table_name
            
        parts = table_name.strip().split('.')
        
        if len(parts) == 1:
            # Only table name provided, add both project and dataset
            return f"{self.project_name}.{self.dataset_name}.{parts[0]}"
        elif len(parts) == 2:
            # Dataset and table provided, add project
            return f"{self.project_name}.{parts[0]}.{parts[1]}"
        else:
            # Already fully qualified or has more parts than expected
            return table_name

    def process_query(self, query: str) -> str:
        """
        Process a query to autocorrect table references when needed.
        This is a simplified approach and may not catch all cases.
        """
        import re
        
        # Match patterns like: FROM table_name, JOIN table_name, etc.
        table_pattern = r'(FROM|JOIN)\s+`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+){0,2})`?'
        
        def replace_table(match):
            clause = match.group(1)  # FROM or JOIN
            table = match.group(2)   # table name
            
            # Format the table name
            formatted_table = self.format_table_name(table)
            
            # Return with backticks for safety
            return f"{clause} `{formatted_table}`"
        
        # Replace all occurrences
        processed_query = re.sub(table_pattern, replace_table, query, flags=re.IGNORECASE)
        return processed_query

    def execute_query(self, query: str):
        """Execute query via POST request to BigQuery endpoint"""
        try:
            # Process query to autocorrect table names
            processed_query = self.process_query(query)
            
            payload = {"query": processed_query}
            response = requests.post(
                self.endpoint_url, 
                json=payload, 
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Extract results from the wrapper if present
            if isinstance(response_data, dict) and 'results' in response_data:
                return response_data['results'][0] if response_data['results'] else {}
            return response_data
        except requests.exceptions.RequestException as e:
            raise Exception(f"BigQuery API request failed: {str(e)}")

    def list_schemas(self):
        print("=======>", LIST_SCHEMA)
        sql_path = Path(LIST_SCHEMA)
        with sql_path.open("r", encoding="utf-8") as f:
            query = f.read()

        try:
            result = self.execute_query(query)
            print("=======>", result)
            return result
        except Exception as e:
            return f"❌ Error listing schemas: {str(e)}"

    def list_database_info(self):
        sql_path = Path(LIST_DATABASE_INFOS)
        with sql_path.open("r", encoding="utf-8") as f:
            query = f.read()

        try:
            result = self.execute_query(query)
            return result
        except Exception as e:
            return f"❌ Error listing database info: {str(e)}"
    
    def list_tables_in_schema(self, schema_name: str):
        sql_path = Path(TABLE_IN_SCHEMA)
        with sql_path.open("r", encoding="utf-8") as f:
            query_template = f.read()

        # Replace parameter placeholder for BigQuery - properly escape the value
        escaped_schema = schema_name.replace("'", "''")  # Basic SQL injection protection
        query = query_template.replace('%(schema_name)s', f"'{escaped_schema}'")
        
        try:
            result = self.execute_query(query)
            return result
        except Exception as e:
            return f"❌ Error listing tables in schema: {str(e)}"
    
    def list_columns_in_table(self, schema_name: str, table_name: str):
        sql_path = Path(COLUMN_IN_TABLE)
        with sql_path.open("r", encoding="utf-8") as f:
            query_template = f.read()

        # Replace parameter placeholders for BigQuery - properly escape the values
        escaped_schema = schema_name.replace("'", "''")
        escaped_table = table_name.replace("'", "''")
        query = query_template.replace('%(schema_name)s', f"'{escaped_schema}'")
        query = query.replace('%(table_name)s', f"'{escaped_table}'")
        
        try:
            result = self.execute_query(query)
            return result
        except Exception as e:
            return f"❌ Error listing columns in table: {str(e)}"
    
    def create_view(self, view_name: str, query: str, validate_only: bool = False):
        """Create or replace a BigQuery view with proper error handling and validation"""
        # Input validation
        if not view_name or not view_name.strip():
            return "❌ View name cannot be empty"
        if not query or not query.strip():
            return "❌ Query cannot be empty"
        
        # Sanitize view name (basic validation)
        if not view_name.replace('_', '').replace('-', '').replace('.', '').isalnum():
            return "❌ View name contains invalid characters. Use only letters, numbers, underscores, hyphens, and dots"
        
        if validate_only:
            # Just validate the query without executing (using dry run)
            try:
                validate_query = f"SELECT * FROM ({query}) LIMIT 0"
                self.execute_query(validate_query)
                return f"✅ Query is valid for view '{view_name}'"
            except Exception as e:
                return f"❌ Invalid query: {str(e)}"
        
        try:
            # Create or replace view in BigQuery
            create_view_query = f"CREATE OR REPLACE VIEW {view_name} AS {query}"
            self.execute_query(create_view_query)
            return f"✅ View '{view_name}' created successfully"
            
        except Exception as e:
            return f"❌ Error creating view '{view_name}': {str(e)}"

    def list_views_detailed(self):
        """List all views with metadata"""
        query = """
        SELECT 
            table_schema,
            table_name,
            view_definition
        FROM `nodal-pod-462214-f0.huggingface_1.INFORMATION_SCHEMA.VIEWS`
        WHERE table_schema NOT IN ('INFORMATION_SCHEMA')
        ORDER BY table_schema, table_name
        """
        try:
            return self.execute_query(query)
        except Exception as e:
            return f"❌ Error listing views: {str(e)}"

    def get_view_content(self, view_name: str, limit: int = 100):
        """Get sample content from a view"""
        try:
            # Format view name
            formatted_view = self.format_table_name(view_name)
            query = f"SELECT * FROM `{formatted_view}` LIMIT {limit}"
            return self.execute_query(query)
        except Exception as e:
            return f"❌ Error querying view: {str(e)}"

    def drop_view(self, view_name: str):
        """Drop a specific view"""
        if not view_name or not view_name.strip():
            return "❌ View name cannot be empty"
        
        try:
            query = f"DROP VIEW IF EXISTS {view_name}"
            self.execute_query(query)
            return f"✅ View '{view_name}' dropped successfully"
        except Exception as e:
            return f"❌ Error dropping view: {str(e)}"

    def execute_sql_file(self, file_path: str):
        """Execute SQL statements from a file"""
        sql_path = Path(file_path)
        if not sql_path.exists():
            return f"❌ SQL file not found: {file_path}"
        
        try:
            with sql_path.open("r", encoding="utf-8") as f:
                sql_content = f.read()
            
            # Split SQL content by semicolon and execute each statement
            sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            executed_commands = []
            
            for command in sql_commands:
                if command:  # Skip empty commands
                    self.execute_query(command)
                    executed_commands.append(command.split()[0:3])  # First few words for logging
            
            return f"✅ Successfully executed {len(executed_commands)} SQL commands"
                    
        except Exception as e:
            return f"❌ Error executing SQL file: {str(e)}"
    
    def create_analytics_views(self):
        """Create all analytics views from SQL file"""
        print("=============>", VIEWS_SQL_FILE)
        if not VIEWS_SQL_FILE:
            return "❌ VIEWS_SQL_FILE_BQ environment variable not set"
        return self.execute_sql_file(VIEWS_SQL_FILE)

    def read_only_query(self, query):
        """Execute read-only query"""
        try:
            result = self.execute_query(query)
            return result
        except Exception as e:
            return f"❌ Error executing query: {str(e)}"
    
    def create_table_from_query(self, table_name: str, source_query: str):
        """Create a table from query in BigQuery (not implemented for safety)"""
        return "❌ Table creation from query is not implemented for BigQuery interface for safety reasons. Use BigQuery console for table operations."

    def drop_table(self, table_name: str):
        """Drop a table in BigQuery (not implemented for safety)"""
        return "❌ Table dropping is not implemented for BigQuery interface for safety reasons. Use BigQuery console for table operations."
