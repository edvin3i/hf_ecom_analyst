import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

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
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SQL query and return results"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    if cursor.description:
                        return [dict(row) for row in cursor.fetchall()]
                    return []
        except Exception as e:
            return [{"error": str(e)}]
    
    def setup_tools(self):
        """Setup MCP tools based on actual schema"""
        
        @self.mcp.tool()
        def analyze_database_schema() -> str:
            """Analyze the complete database schema and structure"""
            try:
                # Get table information with actual schema
                table_query = """
                    SELECT 
                        t.table_name,
                        t.table_type,
                        COUNT(c.column_name) as column_count
                    FROM information_schema.tables t
                    LEFT JOIN information_schema.columns c ON c.table_name = t.table_name
                    WHERE t.table_schema = 'public'
                    GROUP BY t.table_name, t.table_type
                    ORDER BY t.table_name
                """
                
                tables = self.execute_query(table_query)
                
                # Get detailed column info for each table
                detailed_info = {}
                for table in tables:
                    table_name = table['table_name']
                    column_query = """
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = %s
                        ORDER BY ordinal_position
                    """
                    columns = self.execute_query(column_query, (table_name,))
                    detailed_info[table_name] = {
                        'table_type': table['table_type'],
                        'column_count': table['column_count'],
                        'columns': columns
                    }
                
                return json.dumps(detailed_info, indent=2, default=str)
            except Exception as e:
                return f"Error analyzing schema: {str(e)}"
        
        @self.mcp.tool()
        def query_customers(active_only: bool = True, club_member_status: str = "", min_age: int = 0, max_age: int = 100) -> str:
            """Query customers with filters based on actual schema
            
            Args:
                active_only: Filter for active customers only
                club_member_status: Filter by club member status
                min_age: Minimum age filter
                max_age: Maximum age filter
            """
            query = """
                SELECT customer_id, first_name, active, club_member_status, 
                       fashion_news_frequency, age, postal_code
                FROM customers
            """
            where_conditions = []
            params = []
            
            if active_only:
                where_conditions.append("active = %s")
                params.append(True)
                
            if club_member_status:
                where_conditions.append("club_member_status = %s")
                params.append(club_member_status)
                
            if min_age > 0:
                where_conditions.append("age >= %s")
                params.append(min_age)
                
            if max_age < 100:
                where_conditions.append("age <= %s")
                params.append(max_age)
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            query += " ORDER BY customer_id LIMIT 100"
            
            results = self.execute_query(query, tuple(params))
            return json.dumps(results, indent=2, default=str)
        
        @self.mcp.tool()
        def query_articles(product_type: str = "", product_group: str = "", department: str = "") -> str:
            """Query articles with filters based on actual schema
            
            Args:
                product_type: Filter by product type name
                product_group: Filter by product group name  
                department: Filter by department name
            """
            query = """
                SELECT article_id, product_code, prod_name, product_type_name,
                       product_group_name, department_name, colour_group_name,
                       garment_group_name, detail_desc
                FROM articles
            """
            where_conditions = []
            params = []
            
            if product_type:
                where_conditions.append("product_type_name ILIKE %s")
                params.append(f"%{product_type}%")
                
            if product_group:
                where_conditions.append("product_group_name ILIKE %s")
                params.append(f"%{product_group}%")
                
            if department:
                where_conditions.append("department_name ILIKE %s")
                params.append(f"%{department}%")
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            query += " ORDER BY article_id LIMIT 100"
            
            results = self.execute_query(query, tuple(params))
            return json.dumps(results, indent=2, default=str)
        
        @self.mcp.tool()
        def sales_analytics(days_back: int = 30) -> str:
            """Get sales analytics based on actual transaction schema
            
            Args:
                days_back: Number of days to look back for analysis
            """
            query = f"""
                SELECT 
                    DATE_TRUNC('day', transaction_date) as day,
                    COUNT(*) as transaction_count,
                    SUM(price) as total_revenue,
                    AVG(price) as avg_price,
                    COUNT(DISTINCT customer_id) as unique_customers,
                    COUNT(DISTINCT article_id) as unique_articles
                FROM transactions
                WHERE transaction_date >= CURRENT_DATE - INTERVAL '{days_back} days'
                GROUP BY DATE_TRUNC('day', transaction_date)
                ORDER BY day DESC
            """
            
            results = self.execute_query(query)
            return json.dumps(results, indent=2, default=str)
        
        @self.mcp.tool()
        def product_performance(limit: int = 10, days_back: int = 30) -> str:
            """Get top performing products based on actual schema
            
            Args:
                limit: Number of top products to return
                days_back: Number of days to analyze
            """
            query = f"""
                SELECT 
                    a.article_id,
                    a.prod_name,
                    a.product_type_name,
                    a.product_group_name,
                    a.department_name,
                    COUNT(t.article_id) as transaction_count,
                    SUM(t.price) as total_revenue,
                    AVG(t.price) as avg_price,
                    COUNT(DISTINCT t.customer_id) as unique_customers
                FROM articles a
                JOIN transactions t ON a.article_id = t.article_id
                WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '{days_back} days'
                GROUP BY a.article_id, a.prod_name, a.product_type_name, 
                         a.product_group_name, a.department_name
                ORDER BY total_revenue DESC
                LIMIT %s
            """
            
            results = self.execute_query(query, (limit,))
            return json.dumps(results, indent=2, default=str)
        
        @self.mcp.tool()
        def customer_purchase_analysis(customer_id: str = "") -> str:
            """Analyze customer purchase behavior
            
            Args:
                customer_id: Specific customer to analyze (optional)
            """
            if customer_id:
                # Specific customer analysis
                query = """
                    SELECT 
                        c.customer_id,
                        c.first_name,
                        c.active,
                        c.club_member_status,
                        c.age,
                        COUNT(t.article_id) as total_purchases,
                        SUM(t.price) as total_spent,
                        AVG(t.price) as avg_purchase_price,
                        MIN(t.transaction_date) as first_purchase,
                        MAX(t.transaction_date) as last_purchase
                    FROM customers c
                    LEFT JOIN transactions t ON c.customer_id = t.customer_id
                    WHERE c.customer_id = %s
                    GROUP BY c.customer_id, c.first_name, c.active, c.club_member_status, c.age
                """
                results = self.execute_query(query, (customer_id,))
            else:
                # Top customers analysis
                query = """
                    SELECT 
                        c.customer_id,
                        c.first_name,
                        c.active,
                        c.club_member_status,
                        c.age,
                        COUNT(t.article_id) as total_purchases,
                        SUM(t.price) as total_spent,
                        AVG(t.price) as avg_purchase_price
                    FROM customers c
                    JOIN transactions t ON c.customer_id = t.customer_id
                    GROUP BY c.customer_id, c.first_name, c.active, c.club_member_status, c.age
                    ORDER BY total_spent DESC
                    LIMIT 20
                """
                results = self.execute_query(query)
            
            return json.dumps(results, indent=2, default=str)
        
        @self.mcp.tool()
        def sales_channel_analysis() -> str:
            """Analyze sales by channel"""
            query = """
                SELECT 
                    sales_channel_id,
                    COUNT(*) as transaction_count,
                    SUM(price) as total_revenue,
                    AVG(price) as avg_price,
                    COUNT(DISTINCT customer_id) as unique_customers,
                    COUNT(DISTINCT article_id) as unique_articles
                FROM transactions
                GROUP BY sales_channel_id
                ORDER BY total_revenue DESC
            """
            
            results = self.execute_query(query)
            return json.dumps(results, indent=2, default=str)

    def run(self):
        """Run the MCP server"""
        return self.mcp.run()

# Main execution
if __name__ == "__main__":
    print("🤖 Starting E-commerce MCP Server (Correct Schema)...")
    print("📋 Available Tools:")
    print("   - analyze_database_schema")
    print("   - query_customers") 
    print("   - query_articles")
    print("   - sales_analytics")
    print("   - product_performance")
    print("   - customer_purchase_analysis")
    print("   - sales_channel_analysis")
    print("🔌 Ready for Claude Desktop connection!")
    
    server = EcommerceMCPServer()
    server.run() 