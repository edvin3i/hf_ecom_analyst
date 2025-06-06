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
    
api_service = API()

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

def generate_code(user_request: str) -> tuple[Optional[str], str]:
    """Generate and execute Python code using langchain"""
    return api_service.generate_code(user_request)

def generate_graph(graph_type: str, data_dict: Dict) -> tuple[Optional[str], str]:
    """Generate a graph using matplotlib"""
    return api_service.generate_graph(graph_type, data_dict)

def download_file(file_path: str) -> tuple[Optional[str], str]:
    """Download a file from the service"""
    return api_service.download_file(file_path)

# Create the Gradio Blocks interface
with gr.Blocks() as interface:
    with gr.Row():
        with gr.Column(scale=1):
            # Get info on the schema
            discover_input = gr.Textbox(label="Get info on schemas of the database")
            discover_btn = gr.Button("run get infos on the schemas of the database")
            
            # Get info on the database
            database_info = gr.Textbox(label="Get info on the database")
            database_info_btn = gr.Button("Run Get info on the database")
            
            # Get table in schema
            table_in_schema_input = gr.Textbox(label="What schema you want table name for")
            table_in_schema_btn = gr.Button("Run Get list of table in schema")

            # Get Columns in Table
            gr.Markdown("### Get Columns in Table\nRetrieve the columns of a table in a schema.")
            schema_input = gr.Textbox(label="Schema Name")
            table_input = gr.Textbox(label="Table Name")
            column_btn = gr.Button("Get Columns")

            gr.Markdown("### Enter a read-only query")
            query_input = gr.Textbox(label="read-only query")
            query_btn = gr.Button("Get Columns")

            gr.Markdown("### generate a scatter-plot")
            input_text = gr.Textbox(label="Prompt")
            generate_button = gr.Button("Generate")

            gr.Markdown("### generate a code")
            input_text = gr.Textbox(label="Prompt")
            generate_code_button = gr.Button("Generate")

            gr.Markdown("### generate a graph")
            graph_type_input = gr.Textbox(label="Graph Type")
            data_dict_input = gr.Textbox(label="Data Dictionary")
            generate_graph_button = gr.Button("Generate")

            gr.Markdown("### download a file")
            file_path_input = gr.Textbox(label="File Path")
            download_button = gr.Button("Download")
        
        with gr.Column(scale=2):
            schema_info = gr.Textbox(label="Discover DB Output")
            db_info = gr.Textbox(label="Query DB Output")
            table_in_schema = gr.Textbox(label="what table are in the selected schema")
            column_output = gr.Textbox(label="Table Columns Output")
            query_output = gr.Textbox(label="your query output")
            output_image = gr.Image(label="Generated Image", type="filepath")

    # Bind functions to buttons
    discover_btn.click(get_schemas, outputs=schema_info)
    database_info_btn.click(get_db_infos, outputs=db_info)
    table_in_schema_btn.click(get_list_of_tables_in_schema, inputs=table_in_schema_input, outputs=table_in_schema)
    column_btn.click(get_list_of_column_in_table, inputs=[schema_input, table_input], outputs=column_output)
    query_btn.click(run_read_only_query, inputs=query_input, outputs=query_output)
    generate_button.click(fn=serve_image_from_path, outputs=output_image)
    generate_code_button.click(fn=generate_code, inputs=input_text, outputs=code_output)
    generate_graph_button.click(fn=generate_graph, inputs=[graph_type_input, data_dict_input], outputs=graph_output)
    download_button.click(fn=download_file, inputs=file_path_input, outputs=download_output)

# Launch the app
interface.launch(mcp_server=True, share=True)

