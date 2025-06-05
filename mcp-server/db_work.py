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