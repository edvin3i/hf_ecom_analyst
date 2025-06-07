import ast
import gradio as gr
from db_work import DatabaseInterface
import os
from PIL import Image
import var_stats
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

def do_annova(groups, min_sample_size=0):
    '''
		this function runs the annova on the dataset and render the associated F_score and p_value
		groups is a dict that represent the population measures list for each sub-groups. it has the following pattern:
		groups = {
			"type_1": [x_0, x_1, ..., x_n],
			"type_2": [x_0, x_1, ..., x_n],
			"type_3": [x_0, x_1, ..., x_n],
			...,
			"type_p": [x_0, x_1, ..., x_n],
		}

		min_sample_size is used to exclude categories that does not have enough measurement.
		default = 0: all categories are selected

        return type is: dict
        {
            "F-statistic": round(f_stat, 3),
            "p-value": round(p_value, 3)
        }
	'''
    data_dict = ast.literal_eval(groups)

    return var_stats.anova(categories=data_dict, min_sample_size=int(min_sample_size))

def do_tukey_test(groups, min_sample_size=0):
    '''
		this function runs a Tukey's HSD (Honestly Significant Difference) test — a post-hoc analysis following ANOVA. 
	    It tells you which specific pairs of groups differ significantly in their means
        IT is meant to be used after you run a successful anova and you obtain sgnificant F-satatistics and p-value
		categories is a dict that represent the population measures list for each categories. it has the following pattern:
		categories = {
			"type_1": [x_0, x_1, ..., x_n],
			"type_2": [x_0, x_1, ..., x_n],
			"type_3": [x_0, x_1, ..., x_n],
			...,
			"type_p": [x_0, x_1, ..., x_n],
		}

		min_sample_size is used to exclude categories that does not have enough measurement.
		default = 0: all categories are selected

        the return result is the raw dataframe that correspond to the pair wize categorie that reject the hypothesis of non statistically difference between two group
        the signature of the dataframe is the following:
        group1 | group2 | meandiff p-adj | lower | upper | reject (only true)
    
    '''

    data_dict = ast.literal_eval(groups)
    return var_stats.tukey_test(categories=data_dict, min_sample_size=int(min_sample_size))

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

            gr.Markdown("### Enter a read-only query")
            query_input = gr.Textbox(label="read-only query")
            query_btn = gr.Button("Get Columns")

            gr.Markdown("### enter a dict that comply to annova function")
            annova_input = gr.Textbox(label="annova")
            annova_min_sample_input = gr.Textbox(label="min sample size for annova")
            annova_btn = gr.Button("run annova")

            gr.Markdown("### enter a dict that comply to tukey function")
            tukey_input = gr.Textbox(label="tukey")
            tukey_min_sample_input = gr.Textbox(label="min sample size for tukey")
            tukey_btn = gr.Button("run tukey")


        with gr.Column(scale=2):
            schema_info = gr.Textbox(label="Discover DB Output")
            db_info = gr.Textbox(label="Query DB Output")
            table_in_schema = gr.Textbox(label="what table are in the selected schema")
            column_output = gr.Textbox(label="Table Columns Output")
            query_output = gr.Textbox(label="your query output")
            annova_output = gr.Textbox(label="annova output")
            tukey_output = gr.Textbox(label="tukey output")

    # FIXED: Proper function bindings with correct inputs/outputs
    
    # Database operations
    discover_btn.click(get_schemas, outputs=schema_info)
    database_info_btn.click(get_db_infos, outputs=db_info)
    table_in_schema_btn.click(get_list_of_tables_in_schema, inputs=table_in_schema_input, outputs=table_in_schema)
    column_btn.click(get_list_of_column_in_table, inputs=[schema_input, table_input], outputs=column_output)
    query_btn.click(run_read_only_query, inputs=query_input, outputs=query_output)
    annova_btn.click(do_annova, inputs=[annova_input, annova_min_sample_input], outputs=annova_output)
    tukey_btn.click(do_tukey_test, inputs=[tukey_input, tukey_min_sample_input], outputs=tukey_output)

# Launch the app
if __name__ == "__main__":
    print("🚀 Starting E-commerce Database Analytics Platform...")
    print(f"🌐 Dashboard: http://localhost:7860")
    print("🔗 Integrated with FastAPI service for AI analytics")
    
    interface.launch(server_name="0.0.0.0", server_port=7860, mcp_server=True, share=True)

