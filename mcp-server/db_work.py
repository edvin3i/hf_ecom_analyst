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

class EcommerceMCPServer:
    def __init__(self):
        # Initialize FastMCP server
        self.mcp = FastMCP("ecommerce-mcp-server")
        
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'ecommerce_db'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        self.setup_tools()
        
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