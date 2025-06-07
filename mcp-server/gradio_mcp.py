import gradio as gr
from db_work import DatabaseInterface
import os
from PIL import Image
import requests
from typing import Optional, Dict
import json
import time

BASE_URL = "https://beeguy74--example-fastapi-fastapi-app.modal.run"

class API:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def generate_code(self, user_request: str) -> tuple[Optional[str], str]:
        """Generate and execute Python code using langchain"""
        try:
            payload = {"user_request": user_request}
            response = self.session.post(
                f"{self.base_url}/generate-code",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("output", ""), "✅ Code executed successfully"
            else:
                return None, f"❌ Code generation failed: {response.status_code} - {response.text}"
                
        except Exception as e:
            return None, f"❌ Error generating code: {str(e)}"
    
    def generate_graph(self, graph_type: str, data_dict: Dict) -> tuple[Optional[str], str]:
        """Generate a graph using matplotlib"""
        try:
            payload = {
                "graph_type": graph_type,
                "data": json.dumps(data_dict)
            }
            
            response = self.session.post(
                f"{self.base_url}/generate-graph",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                timestamp = int(time.time())
                image_path = f"./graph_{graph_type}_{timestamp}.png"
                with open(image_path, "wb") as f:
                    f.write(response.content)
                return image_path, f"✅ {graph_type.title()} chart generated successfully"
            else:
                return None, f"❌ Graph generation failed: {response.status_code} - {response.text}"
                
        except Exception as e:
            return None, f"❌ Error generating graph: {str(e)}"
    
    def download_file(self, file_path: str) -> tuple[Optional[str], str]:
        """Download a file from the service"""
        try:
            params = {"file_path": file_path}
            response = self.session.get(
                f"{self.base_url}/download-file",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                timestamp = int(time.time())
                local_path = f"./downloaded_{timestamp}_{os.path.basename(file_path)}"
                with open(local_path, "wb") as f:
                    f.write(response.content)
                return local_path, f"✅ File downloaded: {file_path}"
            else:
                return None, f"❌ Download failed: {response.status_code} - {response.text}"
                
        except Exception as e:
            return None, f"❌ Error downloading file: {str(e)}"

# Initialize services
api_service = API(BASE_URL)
db_interface = DatabaseInterface()

# All function definitions (keeping your existing ones)
def get_schemas():
    return db_interface.list_schemas()

def get_db_infos():
    return db_interface.list_database_info()

def get_list_of_tables_in_schema(schema):
    return db_interface.list_tables_in_schema(schema)

def get_list_of_column_in_table(schema, table):
    return db_interface.list_columns_in_table(schema, table)

def run_read_only_query(query: str):
    return db_interface.read_only_query(query)

def create_sample_image():
    img_path = "./sample_graph.png"
    if not os.path.exists(img_path):
        img = Image.new("RGB", (300, 150), color="lightgreen")
        img.save(img_path)
    return img_path

def serve_image_from_path():
    return create_sample_image()

def generate_code_wrapper(user_request: str):
    if not user_request.strip():
        return "❌ Please provide a request", ""
    
    output, status = api_service.generate_code(user_request)
    return output or "No output generated", status

def generate_graph_wrapper(graph_type: str, data_json: str):
    try:
        if not graph_type.strip() or not data_json.strip():
            return None, "❌ Please provide both graph type and data"
        
        data_dict = json.loads(data_json)
        image_path, status = api_service.generate_graph(graph_type, data_dict)
        return image_path, status
        
    except json.JSONDecodeError:
        return None, "❌ Invalid JSON format in data field"
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

def download_file_wrapper(file_path: str):
    if not file_path.strip():
        return "❌ Please provide a file path"
    
    local_path, status = api_service.download_file(file_path)
    return status

def create_analytics_views_from_file():
    try:
        result = db_interface.create_analytics_views()
        return result
    except Exception as e:
        return f"❌ Error creating views: {str(e)}"

# def execute_custom_sql_file(file_path: str):
#     if not file_path.strip():
#         return "❌ Please provide a file path"
#     return db_interface.execute_sql_file(file_path)

# def create_individual_view(view_name: str, view_query: str):
#     return db_interface.create_view(view_name, view_query)

def get_all_views():
    try:
        views = db_interface.list_views_detailed()
        if not views:
            return "No views found in database"
        
        result = []
        for view in views:
            schema, name, owner, definition = view
            short_def = (definition[:100] + "...") if len(definition) > 100 else definition
            result.append(f"📋 {schema}.{name} (Owner: {owner})\n   {short_def}\n")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ Error listing views: {str(e)}"

def get_view_content_sample(view_name: str, limit_str: str = "10"):
    if not view_name.strip():
        return "❌ Please provide a view name"
    
    try:
        limit = int(limit_str) if limit_str.strip() else 10
        limit = min(max(limit, 1), 1000)
        
        content = db_interface.get_view_content(view_name, limit)
        if isinstance(content, str):
            return content
        
        if not content:
            return f"View '{view_name}' exists but contains no data"
        
        result = [f"📊 Sample data from view '{view_name}' (showing {len(content)} rows):\n"]
        for i, row in enumerate(content[:limit], 1):
            result.append(f"Row {i}: {row}")
        
        return "\n".join(result)
    except ValueError:
        return "❌ Invalid limit value - please enter a number"
    except Exception as e:
        return f"❌ Error getting view content: {str(e)}"

def delete_view(view_name: str):
    if not view_name.strip():
        return "❌ Please provide a view name"
    return db_interface.drop_view(view_name)

# TAB 1: Database Operations
with gr.Blocks(title="Database Operations") as tab1:
    gr.Markdown("# 🗄️ Database Operations")
    gr.Markdown("*Explore database schema, tables, and run queries*")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🗄️ Database Schema")
            discover_btn = gr.Button("📋 Get Schemas", variant="primary")
            database_info_btn = gr.Button("ℹ️ Get Database Info", variant="secondary")
            
            gr.Markdown("### 📊 Table Explorer")
            table_in_schema_input = gr.Textbox(label="Schema Name", placeholder="public")
            table_in_schema_btn = gr.Button("Get Tables")
            
            gr.Markdown("### 📄 Column Explorer")
            schema_input = gr.Textbox(label="Schema Name", placeholder="public")
            table_input = gr.Textbox(label="Table Name", placeholder="customers")
            column_btn = gr.Button("Get Columns")
            
            gr.Markdown("### 🔍 SQL Query")
            query_input = gr.Textbox(label="SQL Query", lines=3, placeholder="SELECT * FROM customers LIMIT 10")
            query_btn = gr.Button("Execute Query", variant="primary")
            
            gr.Markdown("### 🎨 Sample Visualization")
            generate_sample_btn = gr.Button("Generate Sample", variant="secondary")
            
        with gr.Column(scale=2):
            schema_info = gr.Textbox(label="📋 Schema Information", lines=5)
            db_info = gr.Textbox(label="ℹ️ Database Information", lines=5)
            table_in_schema = gr.Textbox(label="📊 Tables in Schema", lines=5)
            column_output = gr.Textbox(label="📄 Table Columns", lines=5)
            query_output = gr.Textbox(label="🔍 Query Results", lines=8)
            output_image = gr.Image(label="🎨 Generated Visualization", type="filepath")
    
    # Event handlers for Tab 1
    discover_btn.click(get_schemas, outputs=schema_info)
    database_info_btn.click(get_db_infos, outputs=db_info)
    table_in_schema_btn.click(get_list_of_tables_in_schema, inputs=table_in_schema_input, outputs=table_in_schema)
    column_btn.click(get_list_of_column_in_table, inputs=[schema_input, table_input], outputs=column_output)
    query_btn.click(run_read_only_query, inputs=query_input, outputs=query_output)
    generate_sample_btn.click(serve_image_from_path, outputs=output_image)

# TAB 2: API Operations
with gr.Blocks(title="AI Analytics") as tab2:
    gr.Markdown("# 🤖 AI-Powered Analytics")
    gr.Markdown("*Generate code, create visualizations, and manage files with AI*")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🤖 AI Code Generation")
            code_request_input = gr.Textbox(
                label="Analysis Request", 
                lines=3,
                placeholder="Analyze customer purchase patterns..."
            )
            generate_code_btn = gr.Button("🧠 Generate Code", variant="primary")
            
            gr.Markdown("### 📈 Graph Generation")
            graph_type_input = gr.Textbox(label="Graph Type", placeholder="bar, line, pie, scatter")
            data_dict_input = gr.Textbox(
                label="Data (JSON format)", 
                lines=3,
                placeholder='{"labels": ["A", "B", "C"], "values": [1, 2, 3]}'
            )
            generate_graph_btn = gr.Button("📊 Generate Graph", variant="primary")
            
            gr.Markdown("### 📁 File Download")
            file_path_input = gr.Textbox(label="File Path", placeholder="path/to/file.csv")
            download_btn = gr.Button("📥 Download File", variant="secondary")
            
        with gr.Column(scale=2):
            code_output = gr.Textbox(label="🤖 AI Generated Code/Analysis", lines=10)
            code_status = gr.Textbox(label="Code Status", lines=2)
            graph_output = gr.Image(label="📈 Generated Graph", type="filepath")
            graph_status = gr.Textbox(label="Graph Status", lines=2)
            download_status = gr.Textbox(label="📁 Download Status", lines=3)
    
    # Event handlers for Tab 2
    generate_code_btn.click(
        generate_code_wrapper, 
        inputs=code_request_input, 
        outputs=[code_output, code_status]
    )
    generate_graph_btn.click(
        generate_graph_wrapper, 
        inputs=[graph_type_input, data_dict_input], 
        outputs=[graph_output, graph_status]
    )
    download_btn.click(
        download_file_wrapper, 
        inputs=file_path_input, 
        outputs=download_status
    )

# TAB 3: View Management
with gr.Blocks(title="View Management") as tab3:
    gr.Markdown("# 🗄️ View Management Center")
    gr.Markdown("*Create, manage, and explore database views*")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Analytics Views Management")
            create_analytics_btn = gr.Button("📈 Create All Analytics Views", variant="primary", size="lg")
            
            # gr.Markdown("### 📄 Custom SQL File Execution")
            # sql_file_input = gr.Textbox(
            #     label="SQL File Path", 
            #     placeholder="./sql/custom_queries.sql",
            #     info="Execute SQL commands from file"
            # )
            # execute_sql_file_btn = gr.Button("⚡ Execute SQL File", variant="secondary")
            
            # gr.Markdown("### 🔧 Individual View Creation")
            # new_view_name = gr.Textbox(label="View Name", placeholder="my_custom_view")
            # new_view_query = gr.Textbox(
            #     label="View Query (SQL)", 
            #     lines=4,
            #     placeholder="SELECT * FROM customers WHERE age > 25"
            # )
            # create_single_view_btn = gr.Button("🎯 Create Single View", variant="primary")
            
        with gr.Column(scale=1):
            gr.Markdown("### 📋 View Browser")
            refresh_views_btn = gr.Button("🔄 Refresh View List", variant="secondary")
            
            gr.Markdown("### 🔍 View Content Explorer")
            view_name_input = gr.Textbox(
                label="View Name", 
                placeholder="customer_avg_age_by_article_group",
                info="Enter exact view name"
            )
            content_limit_input = gr.Textbox(
                label="Row Limit", 
                value="10",
                info="Number of rows to display (1-1000)"
            )
            view_content_btn = gr.Button("👁️ Show View Content", variant="secondary")
            
            gr.Markdown("### 🗑️ View Management")
            delete_view_name = gr.Textbox(label="View Name to Delete", placeholder="view_to_delete")
            delete_view_btn = gr.Button("🗑️ Delete View", variant="stop")

    with gr.Row():
        with gr.Column(scale=1):
            views_creation_output = gr.Textbox(
                label="📈 Views Creation Status", 
                lines=5,
                info="Status of analytics views creation"
            )
            sql_file_output = gr.Textbox(
                label="📄 SQL File Execution Results", 
                lines=5,
                info="Results from SQL file execution"
            )
            single_view_output = gr.Textbox(
                label="🎯 Individual View Status", 
                lines=3,
                info="Status of single view creation"
            )
            
        with gr.Column(scale=1):
            views_list_output = gr.Textbox(
                label="📋 Available Views", 
                lines=10,
                info="List of all database views"
            )
            view_content_output = gr.Textbox(
                label="🔍 View Content", 
                lines=10,
                info="Sample data from selected view"
            )
            delete_status_output = gr.Textbox(
                label="🗑️ Deletion Status", 
                lines=2,
                info="View deletion results"
            )

    # Event handlers for Tab 3
    create_analytics_btn.click(
        create_analytics_views_from_file, 
        outputs=views_creation_output
    )

    # execute_sql_file_btn.click(
    #     execute_custom_sql_file, 
    #     inputs=sql_file_input, 
    #     outputs=sql_file_output
    # )

    # create_single_view_btn.click(
    #     create_individual_view,
    #     inputs=[new_view_name, new_view_query],
    #     outputs=single_view_output
    # )

    refresh_views_btn.click(
        get_all_views,
        outputs=views_list_output
    )

    view_content_btn.click(
        get_view_content_sample,
        inputs=[view_name_input, content_limit_input],
        outputs=view_content_output
    )

    delete_view_btn.click(
        delete_view,
        inputs=delete_view_name,
        outputs=delete_status_output
    )

    # Auto-refresh views list when this tab loads
    tab3.load(get_all_views, outputs=views_list_output)

# Create the TabbedInterface
interface = gr.TabbedInterface(
    [tab1, tab2, tab3], 
    tab_names=["🗄️ Database Operations", "🤖 AI Analytics", "📊 View Management"],
    title="E-commerce Database Analytics Platform",
    theme=gr.themes.Soft()
)

# Launch the app
if __name__ == "__main__":
    print("🚀 Starting E-commerce Database Analytics Platform...")
    print(f"🌐 Dashboard: http://localhost:7860")
    print("🔗 Integrated with FastAPI service for AI analytics")
    
    interface.launch(server_name="0.0.0.0", server_port=7860, share=True, mcp_server=True)
