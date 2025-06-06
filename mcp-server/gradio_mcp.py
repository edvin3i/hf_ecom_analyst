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
                # Save the image temporarily
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
                # Save the downloaded file
                timestamp = int(time.time())
                local_path = f"./downloaded_{timestamp}_{os.path.basename(file_path)}"
                with open(local_path, "wb") as f:
                    f.write(response.content)
                return local_path, f"✅ File downloaded: {file_path}"
            else:
                return None, f"❌ Download failed: {response.status_code} - {response.text}"
                
        except Exception as e:
            return None, f"❌ Error downloading file: {str(e)}"

api_service = API(BASE_URL)
db_interface = DatabaseInterface()

# Define the functions
def get_schemas():
    '''
    this function allow you to acknowledge the database schema in order for 
    you to know which schema to query to get the relevant informations
    '''
    return db_interface.list_schemas()

def get_db_infos():
    '''
    this function allow you to acknowledge the relevant database information for you to better understand what is it about
    '''
    return db_interface.list_database_info()

def get_list_of_tables_in_schema(schema):
    """
        this function allows you to get the list of tables (associated with their description if exist) 
        of all the tables that exist in a schema
    """
    return db_interface.list_tables_in_schema(schema)

def get_list_of_column_in_table(schema, table):
    """
        this function allows you to get the list of columns of a specific table of a specific schema.
        each column is associated with its datatype and its description if exist 
    """
    return db_interface.list_columns_in_table(schema, table)

def run_read_only_query(query:str):
    """
        based on what you know about the database properties, you can use this function to run read-only query
        in order to make analysis
        the output is of shape:
        List(Tuple()) where each entry if the list is a row and each entry of the tuple is a column value
    """
    return db_interface.read_only_query(query)

def create_sample_image():
    img_path = "./EuijP.png"
    if not os.path.exists(img_path):
        img = Image.new("RGB", (300, 150), color="lightgreen")
        img.save(img_path)
    return img_path

def serve_image_from_path():
    """
        get a scatter plot of 2 variables.
        input type: [[list_x], [list_y]]
        it is up to you to determine if the variable need to be standardize or not
    """
    return create_sample_image()

def generate_code_wrapper(user_request: str):
    """Wrapper for code generation"""
    if not user_request.strip():
        return "❌ Please provide a request", ""
    
    output, status = api_service.generate_code(user_request)
    return output or "No output generated", status

def generate_graph_wrapper(graph_type: str, data_json: str):
    """Wrapper for graph generation with JSON parsing"""
    try:
        if not graph_type.strip() or not data_json.strip():
            return None, "❌ Please provide both graph type and data"
        
        # Parse the JSON data
        data_dict = json.loads(data_json)
        image_path, status = api_service.generate_graph(graph_type, data_dict)
        return image_path, status
        
    except json.JSONDecodeError:
        return None, "❌ Invalid JSON format in data field"
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

def download_file_wrapper(file_path: str):
    """Wrapper for file download"""
    if not file_path.strip():
        return "❌ Please provide a file path"
    
    local_path, status = api_service.download_file(file_path)
    return status

# Create the Gradio Blocks interface
with gr.Blocks(title="E-commerce Database Analytics", theme=gr.themes.Soft()) as interface:
    gr.Markdown("# 🛍️ E-commerce Database Analytics Platform")
    gr.Markdown("*Database exploration with AI-powered analytics and visualization*")
    
    with gr.Row():
        with gr.Column(scale=1):
            # Database Schema Section
            gr.Markdown("### 🗄️ Database Schema")
            discover_btn = gr.Button("📋 Get Schemas", variant="primary")
            database_info_btn = gr.Button("ℹ️ Get Database Info", variant="secondary")
            
            # Table Explorer Section
            gr.Markdown("### 📊 Table Explorer")
            table_in_schema_input = gr.Textbox(label="Schema Name", placeholder="public")
            table_in_schema_btn = gr.Button("Get Tables")
            
            # Column Explorer Section
            gr.Markdown("### 📄 Column Explorer")
            schema_input = gr.Textbox(label="Schema Name", placeholder="public")
            table_input = gr.Textbox(label="Table Name", placeholder="customers")
            column_btn = gr.Button("Get Columns")
            
            # Query Section
            gr.Markdown("### 🔍 SQL Query")
            query_input = gr.Textbox(label="SQL Query", lines=3, placeholder="SELECT * FROM customers LIMIT 10")
            query_btn = gr.Button("Execute Query", variant="primary")
            
            # Sample Image Section
            gr.Markdown("### 🎨 Sample Visualization")
            generate_sample_btn = gr.Button("Generate Sample", variant="secondary")
            
        with gr.Column(scale=2):
            # Output areas for database operations
            schema_info = gr.Textbox(label="📋 Schema Information", lines=5)
            db_info = gr.Textbox(label="ℹ️ Database Information", lines=5)
            table_in_schema = gr.Textbox(label="📊 Tables in Schema", lines=5)
            column_output = gr.Textbox(label="📄 Table Columns", lines=5)
            query_output = gr.Textbox(label="🔍 Query Results", lines=8)
            output_image = gr.Image(label="🎨 Generated Visualization", type="filepath")
    
    # FIXED: Second row for API operations with proper separation
    with gr.Row():
        with gr.Column(scale=1):
            # AI Code Generation Section
            gr.Markdown("### 🤖 AI Code Generation")
            code_request_input = gr.Textbox(
                label="Analysis Request", 
                lines=3,
                placeholder="Analyze customer purchase patterns..."
            )
            generate_code_btn = gr.Button("🧠 Generate Code", variant="primary")
            
            # Graph Generation Section
            gr.Markdown("### 📈 Graph Generation")
            graph_type_input = gr.Textbox(label="Graph Type", placeholder="bar, line, pie, scatter")
            data_dict_input = gr.Textbox(
                label="Data (JSON format)", 
                lines=3,
                placeholder='{"labels": ["A", "B", "C"], "values": [1, 2, 3]}'
            )
            generate_graph_btn = gr.Button("📊 Generate Graph", variant="primary")
            
            # File Download Section
            gr.Markdown("### 📁 File Download")
            file_path_input = gr.Textbox(label="File Path", placeholder="path/to/file.csv")
            download_btn = gr.Button("📥 Download File", variant="secondary")
            
        with gr.Column(scale=2):
            # FIXED: Added missing output components
            code_output = gr.Textbox(label="🤖 AI Generated Code/Analysis", lines=10)
            code_status = gr.Textbox(label="Code Status", lines=2)
            graph_output = gr.Image(label="📈 Generated Graph", type="filepath")
            graph_status = gr.Textbox(label="Graph Status", lines=2)
            download_status = gr.Textbox(label="📁 Download Status", lines=3)

    # FIXED: Proper function bindings with correct inputs/outputs
    
    # Database operations
    discover_btn.click(get_schemas, outputs=schema_info)
    database_info_btn.click(get_db_infos, outputs=db_info)
    table_in_schema_btn.click(get_list_of_tables_in_schema, inputs=table_in_schema_input, outputs=table_in_schema)
    column_btn.click(get_list_of_column_in_table, inputs=[schema_input, table_input], outputs=column_output)
    query_btn.click(run_read_only_query, inputs=query_input, outputs=query_output)
    generate_sample_btn.click(serve_image_from_path, outputs=output_image)
    
    # API operations
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

# Launch the app
if __name__ == "__main__":
    print("🚀 Starting E-commerce Database Analytics Platform...")
    print(f"🌐 Dashboard: http://localhost:7860")
    print("🔗 Integrated with FastAPI service for AI analytics")
    
    interface.launch(server_name="0.0.0.0", server_port=7860, share=True)

