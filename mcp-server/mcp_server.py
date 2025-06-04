import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from mcp.server import Server
from mcp.types import Tool, TextContent
import gradio as gr
import threading

# Load environment variables
load_dotenv()

class EcommerceMCPServer:
    def __init__(self):
        self.server = Server("ecommerce-mcp-server")
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'ecommerce_db'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        self.schema_cache = {}
        self.suggestions_cache = {}
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
    
    def analyze_database_structure(self) -> Dict[str, Any]:
        """Analyze database structure and relationships"""
        if self.schema_cache:
            return self.schema_cache
            
        structure_analysis = {
            'tables': {},
            'relationships': [],
            'indexes': {},
            'data_patterns': {}
        }
        
        # Get table information
        table_query = """
            SELECT 
                t.table_name,
                t.table_type,
                obj_description(c.oid) as table_comment
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name
        """
        
        tables = self.execute_query(table_query)
        
        for table in tables:
            table_name = table['table_name']
            
            # Get column information
            column_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    col_description(pgc.oid, ordinal_position) as column_comment
                FROM information_schema.columns isc
                LEFT JOIN pg_class pgc ON pgc.relname = isc.table_name
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """
            
            columns = self.execute_query(column_query, (table_name,))
            
            # Get row count and sample data patterns
            try:
                count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
                row_count = self.execute_query(count_query)[0]['row_count']
                
                # Sample data analysis
                sample_query = f"SELECT * FROM {table_name} LIMIT 5"
                sample_data = self.execute_query(sample_query)
                
                structure_analysis['tables'][table_name] = {
                    'columns': columns,
                    'row_count': row_count,
                    'sample_data': sample_data,
                    'table_type': table['table_type']
                }
            except:
                structure_analysis['tables'][table_name] = {
                    'columns': columns,
                    'row_count': 0,
                    'sample_data': [],
                    'table_type': table['table_type']
                }
        
        # Get foreign key relationships
        fk_query = """
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """
        
        relationships = self.execute_query(fk_query)
        structure_analysis['relationships'] = relationships
        
        # Get indexes
        index_query = """
            SELECT
                t.relname as table_name,
                i.relname as index_name,
                array_to_string(array_agg(a.attname), ', ') as column_names,
                ix.indisunique as is_unique
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE t.relkind = 'r'
            AND t.relname NOT LIKE 'pg_%'
            GROUP BY t.relname, i.relname, ix.indisunique
            ORDER BY t.relname, i.relname
        """
        
        indexes = self.execute_query(index_query)
        for idx in indexes:
            table_name = idx['table_name']
            if table_name not in structure_analysis['indexes']:
                structure_analysis['indexes'][table_name] = []
            structure_analysis['indexes'][table_name].append(idx)
        
        self.schema_cache = structure_analysis
        return structure_analysis
    
    def generate_analysis_suggestions(self) -> Dict[str, Any]:
        """Generate intelligent analysis suggestions based on database structure"""
        if self.suggestions_cache:
            return self.suggestions_cache
            
        structure = self.analyze_database_structure()
        suggestions = {
            'business_insights': [],
            'data_quality_checks': [],
            'performance_optimizations': [],
            'suggested_queries': [],
            'kpi_opportunities': []
        }
        
        tables = structure['tables']
        relationships = structure['relationships']
        
        # Analyze business patterns
        if 'customers' in tables and 'transactions' in tables:
            suggestions['business_insights'].extend([
                "Customer lifetime value analysis",
                "Customer acquisition and retention rates",
                "Customer segmentation by purchase behavior",
                "Churn prediction analysis"
            ])
            
            suggestions['suggested_queries'].extend([
                "SELECT customer_id, COUNT(*) as orders, SUM(total_amount) as total_spent FROM transactions GROUP BY customer_id ORDER BY total_spent DESC LIMIT 10",
                "SELECT DATE_TRUNC('month', transaction_date) as month, COUNT(*) as orders, SUM(total_amount) as revenue FROM transactions GROUP BY month ORDER BY month",
                "SELECT AVG(total_amount) as avg_order_value, COUNT(DISTINCT customer_id) as unique_customers FROM transactions"
            ])
        
        if 'articles' in tables or 'products' in tables:
            product_table = 'articles' if 'articles' in tables else 'products'
            suggestions['business_insights'].extend([
                "Product performance analysis",
                "Inventory optimization insights",
                "Category performance comparison",
                "Price elasticity analysis"
            ])
            
            if 'transaction_items' in tables:
                suggestions['suggested_queries'].extend([
                    f"SELECT p.product_name, SUM(ti.quantity) as total_sold, SUM(ti.line_total) as revenue FROM {product_table} p JOIN transaction_items ti ON p.article_id = ti.article_id GROUP BY p.product_name ORDER BY revenue DESC LIMIT 10",
                    f"SELECT category, COUNT(*) as product_count, AVG(price) as avg_price FROM {product_table} GROUP BY category"
                ])
        
        # Data quality suggestions
        for table_name, table_info in tables.items():
            columns = table_info['columns']
            row_count = table_info['row_count']
            
            # Check for potential issues
            nullable_columns = [col['column_name'] for col in columns if col['is_nullable'] == 'YES']
            if nullable_columns:
                suggestions['data_quality_checks'].append(
                    f"Check for NULL values in {table_name}: {', '.join(nullable_columns[:3])}{'...' if len(nullable_columns) > 3 else ''}"
                )
            
            # Check for date columns that might need time-based analysis
            date_columns = [col['column_name'] for col in columns if 'date' in col['data_type'] or 'timestamp' in col['data_type']]
            if date_columns:
                suggestions['kpi_opportunities'].append(
                    f"Time-series analysis opportunity in {table_name} using {date_columns[0]}"
                )
        
        # Performance optimization suggestions
        large_tables = [(name, info) for name, info in tables.items() if info['row_count'] > 10000]
        for table_name, table_info in large_tables:
            if table_name not in structure['indexes'] or len(structure['indexes'].get(table_name, [])) < 2:
                suggestions['performance_optimizations'].append(
                    f"Consider adding indexes to {table_name} (current rows: {table_info['row_count']:,})"
                )
        
        # Relationship-based suggestions
        relationship_map = {}
        for rel in relationships:
            table = rel['table_name']
            if table not in relationship_map:
                relationship_map[table] = []
            relationship_map[table].append(rel['foreign_table_name'])
        
        # Suggest join opportunities
        if len(relationship_map) > 1:
            suggestions['business_insights'].append("Cross-table analysis opportunities identified")
            for table, related in relationship_map.items():
                if len(related) >= 2:
                    suggestions['suggested_queries'].append(
                        f"-- Multi-table analysis starting from {table} (connected to: {', '.join(related)})"
                    )
        
        self.suggestions_cache = suggestions
        return suggestions
    
    def setup_tools(self):
        """Register MCP tools"""
        
        @self.server.tool("analyze_database_schema")
        async def analyze_database_schema() -> List[TextContent]:
            """Analyze complete database structure including tables, columns, relationships, and indexes"""
            structure = self.analyze_database_structure()
            
            # Create a comprehensive schema report
            report = {
                "database_overview": {
                    "total_tables": len(structure['tables']),
                    "total_relationships": len(structure['relationships']),
                    "total_indexes": sum(len(idx_list) for idx_list in structure['indexes'].values())
                },
                "tables": {},
                "relationships": structure['relationships'],
                "data_summary": {}
            }
            
            # Detailed table analysis
            for table_name, table_info in structure['tables'].items():
                report['tables'][table_name] = {
                    "row_count": table_info['row_count'],
                    "column_count": len(table_info['columns']),
                    "columns": [
                        {
                            "name": col['column_name'],
                            "type": col['data_type'],
                            "nullable": col['is_nullable'],
                            "default": col['column_default']
                        } for col in table_info['columns']
                    ],
                    "indexes": structure['indexes'].get(table_name, [])
                }
                
                # Data quality insights
                if table_info['sample_data']:
                    report['data_summary'][table_name] = {
                        "has_data": True,
                        "sample_count": len(table_info['sample_data'])
                    }
            
            return [TextContent(type="text", text=json.dumps(report, indent=2, default=str))]
        
        @self.server.tool("get_analysis_suggestions")
        async def get_analysis_suggestions() -> List[TextContent]:
            """Get intelligent suggestions for database analysis based on structure and data patterns"""
            suggestions = self.generate_analysis_suggestions()
            
            formatted_suggestions = {
                "business_insights": {
                    "description": "Potential business analysis opportunities",
                    "suggestions": suggestions['business_insights']
                },
                "data_quality_checks": {
                    "description": "Recommended data quality validations",
                    "suggestions": suggestions['data_quality_checks']
                },
                "performance_optimizations": {
                    "description": "Database performance improvement opportunities",
                    "suggestions": suggestions['performance_optimizations']
                },
                "kpi_opportunities": {
                    "description": "Key Performance Indicator opportunities",
                    "suggestions": suggestions['kpi_opportunities']
                },
                "suggested_queries": {
                    "description": "Ready-to-use SQL queries for common analysis",
                    "queries": suggestions['suggested_queries']
                }
            }
            
            return [TextContent(type="text", text=json.dumps(formatted_suggestions, indent=2))]
        
        @self.server.tool("execute_suggested_analysis")
        async def execute_suggested_analysis(analysis_type: str, limit: int = 100) -> List[TextContent]:
            """Execute pre-built analysis queries based on database structure"""
            suggestions = self.generate_analysis_suggestions()
            
            if analysis_type == "customer_overview" and 'customers' in self.schema_cache.get('tables', {}):
                query = """
                    SELECT 
                        COUNT(*) as total_customers,
                        COUNT(CASE WHEN customer_status = 'active' THEN 1 END) as active_customers,
                        COUNT(DISTINCT city) as unique_cities,
                        COUNT(DISTINCT country) as unique_countries,
                        MIN(registration_date) as first_registration,
                        MAX(registration_date) as latest_registration
                    FROM customers
                """
                results = self.execute_query(query)
                
            elif analysis_type == "sales_summary" and 'transactions' in self.schema_cache.get('tables', {}):
                query = """
                    SELECT 
                        COUNT(*) as total_transactions,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as avg_transaction_value,
                        COUNT(DISTINCT customer_id) as unique_customers,
                        MIN(transaction_date) as first_transaction,
                        MAX(transaction_date) as latest_transaction,
                        COUNT(CASE WHEN payment_status = 'completed' THEN 1 END) as completed_transactions
                    FROM transactions
                """
                results = self.execute_query(query)
                
            elif analysis_type == "product_inventory" and 'articles' in self.schema_cache.get('tables', {}):
                query = """
                    SELECT 
                        COUNT(*) as total_products,
                        COUNT(DISTINCT category) as unique_categories,
                        SUM(stock_quantity) as total_inventory,
                        AVG(price) as avg_price,
                        COUNT(CASE WHEN stock_quantity = 0 THEN 1 END) as out_of_stock,
                        COUNT(CASE WHEN stock_quantity < 10 THEN 1 END) as low_stock
                    FROM articles
                """
                results = self.execute_query(query)
                
            elif analysis_type == "relationship_analysis":
                structure = self.analyze_database_structure()
                # Create relationship map
                relationship_summary = {}
                for rel in structure['relationships']:
                    table = rel['table_name']
                    if table not in relationship_summary:
                        relationship_summary[table] = []
                    relationship_summary[table].append({
                        'foreign_table': rel['foreign_table_name'],
                        'column': rel['column_name'],
                        'foreign_column': rel['foreign_column_name']
                    })
                
                results = [{"relationship_map": relationship_summary}]
                
            elif analysis_type == "data_quality_report":
                structure = self.analyze_database_structure()
                quality_report = {}
                
                for table_name, table_info in structure['tables'].items():
                    quality_issues = []
                    
                    # Check for tables with no data
                    if table_info['row_count'] == 0:
                        quality_issues.append("Table is empty")
                    
                    # Check for nullable columns
                    nullable_cols = [col['column_name'] for col in table_info['columns'] if col['is_nullable'] == 'YES']
                    if nullable_cols:
                        quality_issues.append(f"Has nullable columns: {', '.join(nullable_cols[:5])}")
                    
                    quality_report[table_name] = {
                        'row_count': table_info['row_count'],
                        'column_count': len(table_info['columns']),
                        'potential_issues': quality_issues
                    }
                
                results = [{"data_quality_report": quality_report}]
                
            else:
                available_analyses = [
                    "customer_overview", "sales_summary", "product_inventory", 
                    "relationship_analysis", "data_quality_report"
                ]
                results = [{"error": f"Unknown analysis type. Available: {', '.join(available_analyses)}"}]
            
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]
        
        @self.server.tool("generate_custom_query")
        async def generate_custom_query(business_question: str) -> List[TextContent]:
            """Generate SQL query suggestions based on business questions and database structure"""
            structure = self.analyze_database_structure()
            tables = list(structure['tables'].keys())
            relationships = structure['relationships']
            
            # Simple pattern matching for common business questions
            question_lower = business_question.lower()
            suggestions = []
            
            if any(word in question_lower for word in ['customer', 'client', 'user']):
                if 'customers' in tables:
                    if 'revenue' in question_lower or 'sales' in question_lower or 'spend' in question_lower:
                        suggestions.append({
                            "query_type": "customer_revenue_analysis",
                            "sql": """
                                SELECT 
                                    c.customer_id,
                                    c.first_name,
                                    c.last_name,
                                    COUNT(t.transaction_id) as total_orders,
                                    SUM(t.total_amount) as total_revenue,
                                    AVG(t.total_amount) as avg_order_value
                                FROM customers c
                                LEFT JOIN transactions t ON c.customer_id = t.customer_id
                                WHERE t.payment_status = 'completed'
                                GROUP BY c.customer_id, c.first_name, c.last_name
                                ORDER BY total_revenue DESC
                                LIMIT 20
                            """,
                            "explanation": "Shows customer revenue analysis with order counts and spending patterns"
                        })
                    
                    if 'segment' in question_lower or 'group' in question_lower:
                        suggestions.append({
                            "query_type": "customer_segmentation",
                            "sql": """
                                SELECT 
                                    CASE 
                                        WHEN total_spent > 1000 THEN 'High Value'
                                        WHEN total_spent > 500 THEN 'Medium Value'
                                        WHEN total_spent > 0 THEN 'Low Value'
                                        ELSE 'No Purchases'
                                    END as customer_segment,
                                    COUNT(*) as customer_count,
                                    AVG(total_spent) as avg_spending
                                FROM (
                                    SELECT 
                                        c.customer_id,
                                        COALESCE(SUM(t.total_amount), 0) as total_spent
                                    FROM customers c
                                    LEFT JOIN transactions t ON c.customer_id = t.customer_id
                                    GROUP BY c.customer_id
                                ) customer_totals
                                GROUP BY customer_segment
                                ORDER BY avg_spending DESC
                            """,
                            "explanation": "Segments customers by spending behavior"
                        })
            
            if any(word in question_lower for word in ['product', 'item', 'article']):
                if 'articles' in tables:
                    if 'best' in question_lower or 'top' in question_lower or 'popular' in question_lower:
                        suggestions.append({
                            "query_type": "top_products",
                            "sql": """
                                SELECT 
                                    a.product_name,
                                    a.category,
                                    a.price,
                                    SUM(ti.quantity) as total_sold,
                                    SUM(ti.line_total) as total_revenue
                                FROM articles a
                                JOIN transaction_items ti ON a.article_id = ti.article_id
                                JOIN transactions t ON ti.transaction_id = t.transaction_id
                                WHERE t.payment_status = 'completed'
                                GROUP BY a.article_id, a.product_name, a.category, a.price
                                ORDER BY total_revenue DESC
                                LIMIT 15
                            """,
                            "explanation": "Shows top-performing products by revenue and quantity sold"
                        })
                    
                    if 'inventory' in question_lower or 'stock' in question_lower:
                        suggestions.append({
                            "query_type": "inventory_analysis",
                            "sql": """
                                SELECT 
                                    category,
                                    COUNT(*) as product_count,
                                    SUM(stock_quantity) as total_inventory,
                                    AVG(stock_quantity) as avg_stock_per_product,
                                    COUNT(CASE WHEN stock_quantity = 0 THEN 1 END) as out_of_stock_count,
                                    COUNT(CASE WHEN stock_quantity < 10 THEN 1 END) as low_stock_count
                                FROM articles
                                GROUP BY category
                                ORDER BY total_inventory DESC
                            """,
                            "explanation": "Analyzes inventory levels by product category"
                        })
            
            if any(word in question_lower for word in ['sales', 'revenue', 'income']):
                if 'transactions' in tables:
                    if 'trend' in question_lower or 'time' in question_lower or 'month' in question_lower:
                        suggestions.append({
                            "query_type": "sales_trends",
                            "sql": """
                                SELECT 
                                    DATE_TRUNC('month', transaction_date) as month,
                                    COUNT(*) as transaction_count,
                                    SUM(total_amount) as monthly_revenue,
                                    AVG(total_amount) as avg_transaction_value,
                                    COUNT(DISTINCT customer_id) as unique_customers
                                FROM transactions
                                WHERE payment_status = 'completed'
                                    AND transaction_date >= CURRENT_DATE - INTERVAL '12 months'
                                GROUP BY DATE_TRUNC('month', transaction_date)
                                ORDER BY month DESC
                            """,
                            "explanation": "Shows monthly sales trends over the past year"
                        })
            
            if not suggestions:
                # Generic suggestion based on available tables
                suggestions.append({
                    "query_type": "general_overview",
                    "sql": f"-- Available tables: {', '.join(tables)}\n-- Sample query for table exploration:",
                    "explanation": f"Your database contains these tables: {', '.join(tables)}. Please provide a more specific business question for targeted query suggestions."
                })
            
            return [TextContent(type="text", text=json.dumps(suggestions, indent=2))]
        
        @self.server.tool("query_customers")
        async def query_customers(filters: Optional[Dict] = None) -> List[TextContent]:
            """Query customer data with optional filters"""
            base_query = """
                SELECT customer_id, first_name, last_name, email, 
                       city, country, registration_date, customer_status
                FROM customers
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if 'city' in filters:
                    where_conditions.append("city ILIKE %s")
                    params.append(f"%{filters['city']}%")
                if 'country' in filters:
                    where_conditions.append("country ILIKE %s")
                    params.append(f"%{filters['country']}%")
                if 'status' in filters:
                    where_conditions.append("customer_status = %s")
                    params.append(filters['status'])
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += " ORDER BY registration_date DESC LIMIT 100"
            
            results = self.execute_query(base_query, tuple(params))
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]
        
        @self.server.tool("query_products")
        async def query_products(filters: Optional[Dict] = None) -> List[TextContent]:
            """Query product/article data with optional filters"""
            base_query = """
                SELECT article_id, product_name, category, brand, price, 
                       stock_quantity, description, status
                FROM articles
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if 'category' in filters:
                    where_conditions.append("category ILIKE %s")
                    params.append(f"%{filters['category']}%")
                if 'min_price' in filters:
                    where_conditions.append("price >= %s")
                    params.append(filters['min_price'])
                if 'max_price' in filters:
                    where_conditions.append("price <= %s")
                    params.append(filters['max_price'])
                if 'in_stock' in filters and filters['in_stock']:
                    where_conditions.append("stock_quantity > 0")
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += " ORDER BY product_name LIMIT 100"
            
            results = self.execute_query(base_query, tuple(params))
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]
        
        @self.server.tool("query_transactions")
        async def query_transactions(filters: Optional[Dict] = None) -> List[TextContent]:
            """Query transaction data with optional filters"""
            base_query = """
                SELECT t.transaction_id, t.customer_id, 
                       c.first_name, c.last_name, c.email,
                       t.transaction_date, t.total_amount, t.payment_method,
                       t.payment_status, t.order_status
                FROM transactions t
                JOIN customers c ON t.customer_id = c.customer_id
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if 'customer_id' in filters:
                    where_conditions.append("t.customer_id = %s")
                    params.append(filters['customer_id'])
                if 'payment_status' in filters:
                    where_conditions.append("t.payment_status = %s")
                    params.append(filters['payment_status'])
                if 'order_status' in filters:
                    where_conditions.append("t.order_status = %s")
                    params.append(filters['order_status'])
                if 'date_from' in filters:
                    where_conditions.append("t.transaction_date >= %s")
                    params.append(filters['date_from'])
                if 'date_to' in filters:
                    where_conditions.append("t.transaction_date <= %s")
                    params.append(filters['date_to'])
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += " ORDER BY t.transaction_date DESC LIMIT 100"
            
            results = self.execute_query(base_query, tuple(params))
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]
        
        @self.server.tool("sales_analytics")
        async def sales_analytics(period: str = "month") -> List[TextContent]:
            """Get sales analytics for specified period"""
            if period == "day":
                date_trunc = "day"
                interval = "7 days"
            elif period == "week":
                date_trunc = "week"
                interval = "8 weeks"
            else:  # month
                date_trunc = "month"
                interval = "12 months"
            
            query = f"""
                SELECT 
                    DATE_TRUNC('{date_trunc}', transaction_date) as period,
                    COUNT(*) as transaction_count,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_transaction_value,
                    COUNT(DISTINCT customer_id) as unique_customers
                FROM transactions
                WHERE transaction_date >= CURRENT_DATE - INTERVAL '{interval}'
                    AND payment_status = 'completed'
                GROUP BY DATE_TRUNC('{date_trunc}', transaction_date)
                ORDER BY period DESC
            """
            
            results = self.execute_query(query)
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]
        
        @self.server.tool("product_performance")
        async def product_performance(limit: int = 10) -> List[TextContent]:
            """Get top performing products"""
            query = """
                SELECT 
                    a.article_id,
                    a.product_name,
                    a.category,
                    a.price,
                    SUM(ti.quantity) as total_sold,
                    SUM(ti.line_total) as total_revenue,
                    COUNT(DISTINCT t.customer_id) as unique_buyers
                FROM articles a
                JOIN transaction_items ti ON a.article_id = ti.article_id
                JOIN transactions t ON ti.transaction_id = t.transaction_id
                WHERE t.payment_status = 'completed'
                GROUP BY a.article_id, a.product_name, a.category, a.price
                ORDER BY total_revenue DESC
                LIMIT %s
            """
            
            results = self.execute_query(query, (limit,))
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]

    def create_gradio_interface(self):
        """Create Gradio web interface"""
        def run_customer_query(city="", country="", status=""):
            filters = {}
            if city: filters['city'] = city
            if country: filters['country'] = country
            if status: filters['status'] = status
            
            query = """
                SELECT customer_id, first_name, last_name, email, 
                       city, country, registration_date, customer_status
                FROM customers
            """
            where_conditions = []
            params = []
            
            if filters:
                if 'city' in filters:
                    where_conditions.append("city ILIKE %s")
                    params.append(f"%{filters['city']}%")
                if 'country' in filters:
                    where_conditions.append("country ILIKE %s")
                    params.append(f"%{filters['country']}%")
                if 'status' in filters:
                    where_conditions.append("customer_status = %s")
                    params.append(filters['status'])
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            query += " ORDER BY registration_date DESC LIMIT 100"
            
            results = self.execute_query(query, tuple(params))
            if results and not any('error' in r for r in results):
                df = pd.DataFrame(results)
                return df
            return pd.DataFrame()
        
        def run_sales_analytics(period):
            if period == "Daily":
                date_trunc = "day"
                interval = "30 days"
            elif period == "Weekly":
                date_trunc = "week"
                interval = "12 weeks"
            else:  # Monthly
                date_trunc = "month"
                interval = "12 months"
            
            query = f"""
                SELECT 
                    DATE_TRUNC('{date_trunc}', transaction_date) as period,
                    COUNT(*) as transaction_count,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_transaction_value
                FROM transactions
                WHERE transaction_date >= CURRENT_DATE - INTERVAL '{interval}'
                    AND payment_status = 'completed'
                GROUP BY DATE_TRUNC('{date_trunc}', transaction_date)
                ORDER BY period DESC
            """
            
            results = self.execute_query(query)
            if results and not any('error' in r for r in results):
                df = pd.DataFrame(results)
                return df
            return pd.DataFrame()
        
        # Create Gradio interface
        with gr.Blocks(title="E-commerce Analytics Dashboard") as interface:
            gr.Markdown("# E-commerce Database Analytics")
            
            with gr.Tab("Customer Analysis"):
                gr.Markdown("## Customer Query Tool")
                with gr.Row():
                    city_input = gr.Textbox(label="City", placeholder="Enter city name")
                    country_input = gr.Textbox(label="Country", placeholder="Enter country")
                    status_input = gr.Dropdown(
                        choices=["", "active", "inactive"], 
                        label="Status", 
                        value=""
                    )
                
                customer_btn = gr.Button("Query Customers")
                customer_output = gr.Dataframe(label="Customer Results")
                
                customer_btn.click(
                    run_customer_query,
                    inputs=[city_input, country_input, status_input],
                    outputs=customer_output
                )
            
            with gr.Tab("Sales Analytics"):
                gr.Markdown("## Sales Performance")
                period_input = gr.Dropdown(
                    choices=["Daily", "Weekly", "Monthly"],
                    label="Period",
                    value="Monthly"
                )
                
                analytics_btn = gr.Button("Generate Analytics")
                analytics_output = gr.Dataframe(label="Sales Analytics")
                
                analytics_btn.click(
                    run_sales_analytics,
                    inputs=period_input,
                    outputs=analytics_output
                )
        
        return interface
    
    async def run_server(self):
        """Run the MCP server"""
        await self.server.run()
    
    def run_gradio(self):
        """Run Gradio interface in separate thread"""
        interface = self.create_gradio_interface()
        interface.launch(
            server_port=int(os.getenv('GRADIO_PORT', 7860)),
            share=False,
            server_name="0.0.0.0"
        )

# Main execution
if __name__ == "__main__":
    server = EcommerceMCPServer()
    
    # Start Gradio in separate thread
    gradio_thread = threading.Thread(target=server.run_gradio)
    gradio_thread.daemon = True
    gradio_thread.start()
    
    # Run MCP server
    asyncio.run(server.run_server())