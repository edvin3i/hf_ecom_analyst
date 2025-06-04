import os
import pandas as pd
import gradio as gr
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict

# Load environment variables
load_dotenv()

class EcommerceDashboard:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'ecommerce_db'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
    
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
    
    def run_customer_query(self, active_only, club_status, min_age, max_age):
        """Query customers with correct schema"""
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
            
        if club_status and club_status != "All":
            where_conditions.append("club_member_status = %s")
            params.append(club_status)
            
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
        if results and not any('error' in r for r in results):
            return pd.DataFrame(results)
        return pd.DataFrame()
    
    def run_sales_analytics(self, days_back):
        """Get sales analytics with correct schema"""
        query = f"""
            SELECT 
                DATE_TRUNC('day', transaction_date) as day,
                COUNT(*) as transaction_count,
                SUM(price) as total_revenue,
                AVG(price) as avg_price,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM transactions
            WHERE transaction_date >= CURRENT_DATE - INTERVAL '{days_back} days'
            GROUP BY DATE_TRUNC('day', transaction_date)
            ORDER BY day DESC
        """
        
        results = self.execute_query(query)
        if results and not any('error' in r for r in results):
            return pd.DataFrame(results)
        return pd.DataFrame()
    
    def run_product_analysis(self, product_type, department):
        """Analyze products with correct schema"""
        query = """
            SELECT 
                a.article_id,
                a.prod_name,
                a.product_type_name,
                a.product_group_name,
                a.department_name,
                COUNT(t.article_id) as transaction_count,
                SUM(t.price) as total_revenue,
                AVG(t.price) as avg_price
            FROM articles a
            LEFT JOIN transactions t ON a.article_id = t.article_id
        """
        where_conditions = []
        params = []
        
        if product_type and product_type != "All":
            where_conditions.append("a.product_type_name = %s")
            params.append(product_type)
            
        if department and department != "All":
            where_conditions.append("a.department_name = %s")
            params.append(department)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += """
            GROUP BY a.article_id, a.prod_name, a.product_type_name, 
                     a.product_group_name, a.department_name
            ORDER BY total_revenue DESC NULLS LAST
            LIMIT 50
        """
        
        results = self.execute_query(query, tuple(params))
        if results and not any('error' in r for r in results):
            return pd.DataFrame(results)
        return pd.DataFrame()
    
    def export_results(self, df, filename_prefix):
        """Export results to CSV"""
        if df.empty:
            return "No data to export"
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        df.to_csv(filepath, index=False)
        return f"Exported to {filename}"
    
    def get_club_statuses(self):
        """Get unique club member statuses"""
        query = "SELECT DISTINCT club_member_status FROM customers WHERE club_member_status IS NOT NULL ORDER BY club_member_status"
        results = self.execute_query(query)
        statuses = ["All"] + [r['club_member_status'] for r in results if r.get('club_member_status')]
        return statuses
    
    def get_product_types(self):
        """Get unique product types"""
        query = "SELECT DISTINCT product_type_name FROM articles WHERE product_type_name IS NOT NULL ORDER BY product_type_name"
        results = self.execute_query(query)
        types = ["All"] + [r['product_type_name'] for r in results if r.get('product_type_name')]
        return types
    
    def get_departments(self):
        """Get unique departments"""
        query = "SELECT DISTINCT department_name FROM articles WHERE department_name IS NOT NULL ORDER BY department_name"
        results = self.execute_query(query)
        departments = ["All"] + [r['department_name'] for r in results if r.get('department_name')]
        return departments
    
    def create_interface(self):
        """Create Gradio interface with correct schema"""
        with gr.Blocks(title="E-commerce Analytics Dashboard", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🛍️ E-commerce Business Intelligence Dashboard")
            
            with gr.Tab("👥 Customer Analytics"):
                gr.Markdown("## Customer Analysis")
                
                with gr.Row():
                    active_only = gr.Checkbox(label="🟢 Active Customers Only", value=True)
                    club_status = gr.Dropdown(
                        choices=self.get_club_statuses(),
                        label="👑 Club Member Status",
                        value="All"
                    )
                
                with gr.Row():
                    min_age = gr.Number(label="📅 Min Age", value=0, minimum=0, maximum=100)
                    max_age = gr.Number(label="📅 Max Age", value=100, minimum=0, maximum=100)
                
                customer_btn = gr.Button("🔍 Query Customers", variant="primary")
                customer_output = gr.Dataframe(label="Customer Results")
                
                export_customer_btn = gr.Button("📥 Export Customer Data")
                export_status = gr.Textbox(label="Export Status", interactive=False)
                
                customer_btn.click(
                    self.run_customer_query,
                    inputs=[active_only, club_status, min_age, max_age],
                    outputs=customer_output
                )
                
                export_customer_btn.click(
                    lambda df: self.export_results(df, "customers"),
                    inputs=customer_output,
                    outputs=export_status
                )
            
            with gr.Tab("💰 Sales Analytics"):
                gr.Markdown("## Sales Performance Analysis")
                
                days_back = gr.Slider(
                    minimum=7,
                    maximum=365,
                    value=30,
                    step=1,
                    label="📅 Days to Analyze"
                )
                
                analytics_btn = gr.Button("📈 Generate Sales Analytics", variant="primary")
                analytics_output = gr.Dataframe(label="Sales Analytics")
                
                export_sales_btn = gr.Button("📥 Export Sales Data")
                sales_export_status = gr.Textbox(label="Export Status", interactive=False)
                
                analytics_btn.click(
                    self.run_sales_analytics,
                    inputs=days_back,
                    outputs=analytics_output
                )
                
                export_sales_btn.click(
                    lambda df: self.export_results(df, "sales_analytics"),
                    inputs=analytics_output,
                    outputs=sales_export_status
                )
            
            with gr.Tab("🛍️ Product Analytics"):
                gr.Markdown("## Product Performance Analysis")
                
                with gr.Row():
                    product_type = gr.Dropdown(
                        choices=self.get_product_types(),
                        label="👕 Product Type",
                        value="All"
                    )
                    department = gr.Dropdown(
                        choices=self.get_departments(),
                        label="🏢 Department",
                        value="All"
                    )
                
                product_btn = gr.Button("📊 Analyze Products", variant="primary")
                product_output = gr.Dataframe(label="Product Analysis")
                
                export_product_btn = gr.Button("📥 Export Product Data")
                product_export_status = gr.Textbox(label="Export Status", interactive=False)
                
                product_btn.click(
                    self.run_product_analysis,
                    inputs=[product_type, department],
                    outputs=product_output
                )
                
                export_product_btn.click(
                    lambda df: self.export_results(df, "product_analysis"),
                    inputs=product_output,
                    outputs=product_export_status
                )
        
        return interface

if __name__ == "__main__":
    print("📊 Starting E-commerce Gradio Dashboard (Correct Schema)...")
    print(f"🌐 Dashboard will be available at: http://localhost:{os.getenv('GRADIO_PORT', 7860)}")
    
    dashboard = EcommerceDashboard()
    interface = dashboard.create_interface()
    
    interface.launch(
        server_port=int(os.getenv('GRADIO_PORT', 7860)),
        share=False,
        server_name="0.0.0.0"
    ) 