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

# Global state for database connection
db_interface = None
db_connection_status = "❌ Not Connected"

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
                timeout=120
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
                timeout=120
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
                timeout=120
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

def setup_database_connection(host: str, port: str, database: str, user: str, password: str):
	"""Setup database connection with user-provided configuration"""
	global db_interface, db_connection_status
	
	if not all([host.strip(), port.strip(), database.strip(), user.strip(), password.strip()]):
		db_connection_status = "❌ All fields are required"
		return db_connection_status, False
	
	try:
		db_config = {
			'host': host.strip(),
			'port': int(port.strip()),
			'database': database.strip(),
			'user': user.strip(),
			'password': password.strip()
		}
		
		# Test connection
		test_interface = DatabaseInterface(db_config)
		test_connection = test_interface.get_db_connection()
		test_connection.close()
		
		# If successful, set global interface
		db_interface = test_interface
		db_connection_status = f"✅ Connected to {database} at {host}:{port}"
		return db_connection_status, True
		
	except ValueError:
		db_connection_status = "❌ Port must be a valid number"
		return db_connection_status, False
	except Exception as e:
		db_connection_status = f"❌ Connection failed: {str(e)}"
		return db_connection_status, False

def get_connection_status():
	"""Get current database connection status"""
	return db_connection_status

def check_db_connection():
	"""Check if database is connected before operations"""
	if db_interface is None:
		return False, "❌ Please configure database connection first"
	return True, "✅ Database connected"

# Initialize services
api_service = API(BASE_URL)

# Updated database functions with connection checks
def get_schemas():
	"""### `get_schemas()`"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_schemas()

def get_db_infos():
	"""### `get_db_infos()`"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_database_info()

def get_list_of_tables_in_schema(schema):
	"""### `get_list_of_tables_in_schema(schema_name: str)`"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_tables_in_schema(schema)

def get_list_of_column_in_table(schema, table):
	"""### `get_list_of_column_in_table(schema_name: str, table_name: str)`"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_columns_in_table(schema, table)

def run_read_only_query(query: str):
	"""### `run_read_only_query(query: str)`"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.read_only_query(query)

def create_table_from_query(table_name: str, source_query: str):
	"""### `create_table_from_query(table_name: str, source_query: str)`"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.create_table_from_query(table_name, source_query)

def drop_table(table_name: str):
	"""### `drop_table(table_name: str)`"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.drop_table(table_name)

def create_sample_image():
    img_path = "./sample_graph.png"
    if not os.path.exists(img_path):
        img = Image.new("RGB", (300, 150), color="lightgreen")
        img.save(img_path)
    return img_path

def serve_image_from_path():
    """Serve the sample image"""
    return create_sample_image()

def do_annova(table_name, min_sample_size=0):
    '''
        this function runs the annova on the dataset and render the associated F_score and p_value
        table_name is the name of the table on which you want to run the ANOVA
        the selected table MUST have the following signature:

        groups | measurement

        exemple with the product_type_age table:

        type | age
        ----------
        'Coat', '36'
        'Coat', '36'
        'Hat/beanie', '32'
        ...

        min_sample_size is used to exclude categories that does not have enough measurement.
        default = 0: all categories are selected

        return type is: dict
        {
            "F-statistic": round(f_stat, 3),
            "p-value": round(p_value, 3)
        }
    '''
    return var_stats.anova(db_interface, table_name=table_name, min_sample_size=int(min_sample_size))

def do_tukey_test(table_name, min_sample_size=0):
    '''
        this function runs a Tukey's HSD (Honestly Significant Difference) test — a post-hoc analysis following ANOVA. 
        It tells you which specific pairs of groups differ significantly in their means
        IT is meant to be used after you run a successful anova and you obtain sgnificant F-satatistics and p-value
        table_name is the name of the table on which you want to run the ANOVA
        the selected table MUST have the following signature:

        groups | measurement

        exemple with the product_type_age table:

        type | age
        ----------
        'Coat', 36
        'Coat', 36
        'Hat/beanie', 32
        ...

        min_sample_size is used to exclude categories that does not have enough measurement.
        default = 0: all categories are selected

        the return result is the raw dataframe that correspond to the pair wize categorie that reject the hypothesis of non statistically difference between two group
        the signature of the dataframe is the following:
        group1 | group2 | meandiff p-adj | lower | upper | reject (only true)
    
    '''
    return var_stats.tukey_test(db_interface, table_name=table_name, min_sample_size=int(min_sample_size))

def do_tsne_embedding(query):
    """

        this tool allow to run a TSNE dimensionality reduction algorythme and a clustering (HDBSCAN) on top of that.

        the input query, is a sql query that MUST return a table with at least the item id and the corresponding embeddding.
        FOR COMPUTATIONAL PURPOSE, THE QUERY YOU SEND MUST NOT RETURN A TABLE GREATER THAN 500 OUTPUT ROWS
        exemple:
        result = db_connection.read_only_query(query)
        result shape:
        article_id | embedding
        0125456    | [0.3, 0.5 ...]

        the return is a dictionnary that has the following format:

            return {
                "ids": ids,
                "x_axis": tsne_projection_x_list,
                "y_axis": tsne_projection_y_list,
                "labels": labels
            }
    """

    return var_stats.embedding_clustering(db_interface, query)

def do_vector_centroid(query):
    """
        this tool allow you to compute the centroid of a list of embedding vectors
        the input query, is a sql query that MUST return a table with only 1 column, the embeddings.
        exemple:
        result = db_connection.read_only_query(query)
        result shape:
         embedding
         [0.3, 0.5 ...]

        the return value is the computed centroid vector, that you can use to work with.
    """
    return var_stats.vector_centroid(db_interface, query)

def embed_text_modal_api(text):
    """
        This function allows you to send a list of text to be embeded by our 
        external model.
        the format should be the following:
        [
        "text_to_embed 1",
        "text_to_embed 2",
        "text_to_embed 3",
        ...
        ]
        the return is the vector embedding corresponding to the text you input or a list of vector in case you gave a list of text.
        thoses vectors are compatible with the one you can find in the database and can be used to be compared with vectors you'll get by querying the database.
    
    """
    to_list = ast.literal_eval(text)
    response = requests.post(
        "https://beeguy74--embeddings-api-fastapi-app.modal.run/embed",  # Replace with actual URL
        json={"texts": to_list}
    )
    if response.status_code != 200:
        return f"Embedding API failed: {response.status_code} - {response.text}"
    embeddings = response.json().get("embeddings")

    return embeddings

def generate_code_wrapper(user_request: str):
    """
        ### `generate_code_wrapper(user_request: str)`
        - **Purpose**: Generate Python code based on user request
        - **Parameters**: `user_request` - Textual description of the analysis
        - **Returns**: Generated code and status message
        - **Use Case**: AI-powered code generation for data analysis"""
    if not user_request.strip():
        return "❌ Please provide a request", ""
    
    output, status = api_service.generate_code(user_request)
    return output or "No output generated", status

def generate_graph_wrapper(graph_type: str, data_json: str):
    """
        ### `generate_graph_wrapper(graph_type: str, data_json: str)`
        - **Purpose**: Create visualizations using matplotlib
        - **Parameters**: `graph_type` - Type of chart (bar, line, pie, scatter)
        - **Returns**: Image file path and status
        - **Use Case**: Creating charts and graphs for presentations"""
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

def query_and_generate_graph_wrapper(query: str, graph_type: str):
    """
    Executes a SQL query and generates a graph visualization from the results.
    This function is particularly useful when query results are too large for the context window
    or when visual representation of data is preferred over tabular format.
    Args:
        query (str): SQL query to execute. Must return at least two columns where the first
                    column represents labels and the second represents values.
        graph_type (str): Type of graph to generate (e.g., 'bar', 'line', 'pie', etc.).
    Returns:
        tuple: A tuple containing:
            - image_path (str or None): Path to the generated graph image if successful, None if failed
            - status (str): Status message indicating success or error details
    """
    if not query.strip():
        return None, "❌ Please provide a SQL query."
    if not graph_type.strip():
        return None, "❌ Please provide a graph type."

    query_result = run_read_only_query(query)

    if isinstance(query_result, str) and query_result.startswith("❌"):
        return None, f"❌ Query execution failed: {query_result}"
    
    if not query_result:
        return None, "❌ Query returned no data."

    data_dict = {}
    try:
        if isinstance(query_result, list) and len(query_result) > 0:
            # Assuming first column is labels, second is values
            # And that there are headers in the first row of the result if it's a list of lists/tuples
            if isinstance(query_result[0], (list, tuple)) and len(query_result[0]) >= 2:
                # Check if the first row looks like headers (strings)
                if all(isinstance(item, str) for item in query_result[0]):
                    headers = query_result[0]
                    data_rows = query_result[1:]
                else: # No headers, assume first col labels, second values
                    headers = ["labels", "values"] # default headers
                    data_rows = query_result

                if not data_rows:
                        return None, "❌ Query returned headers but no data rows."

                data_dict["labels"] = [str(row[0]) for row in data_rows]
                data_dict["values"] = [row[1] for row in data_rows] # Keep original type for values
            else:
                return None, "❌ Query result format not suitable for graphing (PostgreSQL). Expected at least two columns."
        else:
            return None, "❌ Query returned no data or unexpected format (PostgreSQL)."

        if not data_dict.get("labels") or not data_dict.get("values"):
            return None, "❌ Failed to extract labels and values from query result."

        image_path, status = api_service.generate_graph(graph_type, data_dict)
        return image_path, status

    except Exception as e:
        return None, f"❌ Error processing query result or generating graph: {str(e)}"


def download_file_wrapper(file_path: str):
    """### `download_file_wrapper(file_path: str)` 
    - **Purpose**: Download files from the service 
    - **Use Case**: Retrieving generated reports or datasets"""
    if not file_path.strip():
        return "❌ Please provide a file path"
    
    local_path, status = api_service.download_file(file_path)
    return status

def get_mcp_server_instructions():
    """
    Returns comprehensive usage guidelines and documentation for all MCP server functions.
    Call this function first to understand available tools, workflows, and best practices.
    
    This function provides:
    - Complete function documentation
    - Recommended workflows  
    - Best practices for MCP clients
    - Database schema information
    - Statistical analysis guidelines
    """
    return """
    ## Purpose
            This MCP server provides comprehensive e-commerce database analytics capabilities, enabling clients to explore database schemas, run queries, perform statistical analysis, and generate AI-powered insights. The server is designed to help users analyze customer behavior, sales patterns, and business metrics from e-commerce data.
                    
            ## 🎯 Use Cases
            This MCP server is designed for:
            - **E-commerce Analytics**: Customer behavior, sales patterns, product performance
            - **Business Intelligence**: KPI tracking, trend analysis, forecasting
            - **Statistical Research**: Hypothesis testing, comparative analysis
            - **Data Exploration**: Schema discovery, data profiling, relationship analysis
            - **AI-Assisted Insights**: Natural language to analysis, automated reporting
                    
            ## 📊 Database Schema & Discovery Functions
            ### `get_schemas()`**Purpose**: Retrieve all database schemas
            ### `get_db_infos()` **Purpose**: Get comprehensive database information and metadata
            ### `get_list_of_tables_in_schema(schema_name: str)` **Purpose**: List all tables within a specific schema
            ### `get_list_of_column_in_table(schema_name: str, table_name: str)` **Purpose**: Get detailed column information for a specific table

            ## 🔍 Query & Data Manipulation Functions
            ### `run_read_only_query(query: str)` **Purpose**: Execute read-only SQL queries safely
            ### `create_table_from_query(table_name: str, source_query: str)` **Purpose**: Create permanent tables from SELECT queries
            ### `drop_table(table_name: str)` **Purpose**: Remove tables from the database- **Use Case**: Cleaning up temporary analysis tables

            ## 📈 Statistical Analysis Functions
            ### `do_annova(table_name: str, min_sample_size: int = 0)` **Purpose**: Perform ANOVA (Analysis of Variance) statistical test- **Use Case**: Testing if there are significant differences between group means
            ### `do_tukey_test(table_name: str, min_sample_size: int = 0)` **Purpose**: Perform Tukey's HSD post-hoc analysis after ANOVA **Use Case**: Identifying which specific groups differ significantly **Prerequisite**: Should be used after significant ANOVA results

            ## 🤖 AI-Powered Analytics Functions
            ### `generate_code_wrapper(user_request: str)`- **Purpose**: Generate and execute Python code using AI based on natural language requests
            ### `generate_graph_wrapper(graph_type: str, data_json: str)`- **Purpose**: Create visualizations using matplotlib **Use Case**: Creating charts and graphs for presentations- **Example**: `{"labels": ["Q1", "Q2", "Q3"], "values": [100, 150, 200]}`
            ### `download_file_wrapper(file_path: str)`- **Purpose**: Download files from the analytics service

            ## 🔄 Recommended Workflows
            ### 1. Discovery Workflow
            get_schemas() → Discover available schemas
            get_list_of_tables_in_schema("public") → Find tables
            get_list_of_column_in_table("public", "customers") → Understand structure
            run_read_only_query("SELECT * FROM customers LIMIT 5") → Sample data

            ### 2. Analysis Workflow
            run_read_only_query() → Explore data
            create_table_from_query() → Create analysis datasets
            do_annova() → Statistical testing
            do_tukey_test() → Post-hoc analysis
            generate_graph_wrapper() → Visualize results
            
            ### 3. AI-Assisted Analysis
            generate_code_wrapper("Analyze customer segments") → Get AI insights
            Use results to guide further manual analysis
            generate_graph_wrapper() → Visualize AI findings
                                 
            ## ✅ Best Practices for MCP Clients
            1. **Start with Discovery**: Always begin by exploring schemas and tables before analysis
            2. **Use Read-Only Queries**: Prefer `run_read_only_query()` for exploration to maintain data safety
            3. **Statistical Validation**: Use `do_annova()` before `do_tukey_test()` for proper statistical workflow
            4. **AI Enhancement**: Use `generate_code_wrapper()` for complex analysis that would be difficult to code manually
            5. **Clean Up**: Use `drop_table()` to remove temporary analysis tables when done
            6. **Error Handling**: All functions return status indicators - check for errors before proceeding
            7. **Data Safety**: Core tables (transactions, customers, articles) are protected from modification"""

# TAB 0: Database Configuration
with gr.Blocks(title="Database Configuration") as tab0:
	gr.Markdown("# 🔌 Database Configuration")
	gr.Markdown("*Configure your database connection before using the analytics platform*")
	
	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 🗄️ Database Connection")
			host_input = gr.Textbox(label="Host", placeholder="database.example.com", value="")
			port_input = gr.Textbox(label="Port", placeholder="5432", value="")
			database_input = gr.Textbox(label="Database", placeholder="my_database", value="")
			user_input = gr.Textbox(label="User", placeholder="db_user", value="")
			password_input = gr.Textbox(label="Password", type="password", placeholder="••••••••", value="")
			
			connect_btn = gr.Button("🔌 Connect to Database", variant="primary")
			
		with gr.Column(scale=1):
			connection_status = gr.Textbox(label="🔌 Connection Status", value=db_connection_status, interactive=False)
			gr.Markdown("### ℹ️ Instructions")
			gr.Markdown("""
			1. **Fill in your database credentials**
			2. **Click 'Connect to Database'**
			3. **Wait for successful connection**
			4. **Proceed to other tabs once connected**
			
			**Note**: All database operations require a valid connection.
			""")
	
	def handle_connection(host, port, database, user, password):
		status, success = setup_database_connection(host, port, database, user, password)
		return status
	
	connect_btn.click(
		handle_connection,
		inputs=[host_input, port_input, database_input, user_input, password_input],
		outputs=connection_status
	)

# TAB 1: Database Operations
with gr.Blocks(title="Database Operations") as tab1:
    gr.Markdown("# 🗄️ Database Operations")
    gr.Markdown("*Explore database schema, tables, and run queries*")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🗄️ Database Schema")
            discover_btn = gr.Button("📋 Get Schemas", variant="primary")
            database_info_btn = gr.Button("ℹ️ Get Database Info", variant="secondary")
        with gr.Column(scale=2):
            schema_info = gr.Textbox(label="📋 Schema Information", lines=5)
            db_info = gr.Textbox(label="ℹ️ Database Information", lines=5)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Table Explorer")
            table_in_schema_input = gr.Textbox(label="Schema Name", placeholder="public")
            table_in_schema_btn = gr.Button("Get Tables")

        with gr.Column(scale=2):
            table_in_schema = gr.Textbox(label="📊 Tables in Schema", lines=5)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📄 Column Explorer")
            schema_input = gr.Textbox(label="Schema Name", placeholder="public")
            table_input = gr.Textbox(label="Table Name", placeholder="customers")
            column_btn = gr.Button("Get Columns")

        with gr.Column(scale=2):
            column_output = gr.Textbox(label="📄 Table Columns", lines=5)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🔍 SQL Query")
            query_input = gr.Textbox(label="SQL Query", lines=3, placeholder="SELECT * FROM customers LIMIT 10")
            query_btn = gr.Button("Execute Query", variant="primary")

        with gr.Column(scale=2):
            query_output = gr.Textbox(label="🔍 Query Results", lines=8)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🔍 Create Table")
            table_name_input = gr.Textbox(label="Table Name", placeholder="table")
            source_query_input = gr.Textbox(label="Source Query", lines=3, placeholder="SELECT * FROM customers LIMIT 10")
            create_table_from_query_btn = gr.Button("Create Table", variant="primary")

        with gr.Column(scale=2):
            table_status = gr.Textbox(label="table status")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🔍 Drop Table")
            drop_table_name_input = gr.Textbox(label="Table Name", placeholder="table")
            drop_table_btn = gr.Button("Drop Table", variant="primary")
            
            gr.Markdown("### 🎨 Sample Visualization")
            generate_sample_btn = gr.Button("Generate Sample", variant="secondary")
            
        with gr.Column(scale=2):
            drop_table_status = gr.Textbox(label="drop table status")
            output_image = gr.Image(label="🎨 Generated Visualization", type="filepath")
    
    # Event handlers for Tab 1
    discover_btn.click(get_schemas, outputs=schema_info)
    database_info_btn.click(get_db_infos, outputs=db_info)
    table_in_schema_btn.click(get_list_of_tables_in_schema, inputs=table_in_schema_input, outputs=table_in_schema)
    column_btn.click(get_list_of_column_in_table, inputs=[schema_input, table_input], outputs=column_output)
    query_btn.click(run_read_only_query, inputs=query_input, outputs=query_output)
    generate_sample_btn.click(serve_image_from_path, outputs=output_image)
    create_table_from_query_btn.click(create_table_from_query, inputs=[table_name_input, source_query_input], outputs=table_status)
    drop_table_btn.click(drop_table, inputs=drop_table_name_input, outputs=drop_table_status)

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

        with gr.Column(scale=2):
            code_output = gr.Textbox(label="🤖 AI Generated Code/Analysis", lines=10)
            code_status = gr.Textbox(label="Code Status", lines=2)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📈 Graph Generation")
            graph_type_input = gr.Textbox(label="Graph Type", placeholder="bar, line, pie, scatter")
            data_dict_input = gr.Textbox(
                label="Data (JSON format)", 
                lines=3,
                placeholder='{"labels": ["A", "B", "C"], "values": [1, 2, 3]}'
            )
            generate_graph_btn = gr.Button("📊 Generate Graph", variant="primary")
            gr.Markdown("### 🔍 Query & Generate Graph")
            query_for_graph_input = gr.Textbox(
                label="SQL Query for Graph",
                lines=3,
                placeholder="SELECT category, COUNT(*) FROM sales GROUP BY category"
            )
            graph_type_for_query_input = gr.Textbox(label="Graph Type", placeholder="bar, line, pie, scatter")
            query_and_graph_btn = gr.Button("📈 Query & Generate Graph", variant="primary")

        with gr.Column(scale=2):
            graph_output = gr.Image(label="📈 Generated Graph", type="filepath")
            graph_status = gr.Textbox(label="Graph Status", lines=2)
            
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📁 File Download")
            file_path_input = gr.Textbox(label="File Path", placeholder="path/to/file.csv")
            download_btn = gr.Button("📥 Download File", variant="secondary")

            gr.Markdown("### 📍​ Embed text")
            embed_text_input = gr.Textbox(label="Text to embed", placeholder="lorem ipsum")
            embed_btn = gr.Button("📍​ Embed text", variant="secondary")
            
        with gr.Column(scale=2):
            download_status = gr.Textbox(label="📁 Download Status", lines=3)
            embed_text = gr.Textbox(label="Vector")
    
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
    embed_btn.click(
        embed_text_modal_api,
        inputs=embed_text_input,
        outputs=embed_text
        )
    query_and_graph_btn.click(
        query_and_generate_graph_wrapper,
        inputs=[query_for_graph_input, graph_type_for_query_input],
        outputs=[graph_output, graph_status]
    )

# TAB 4: Statistical Analysis
with gr.Blocks(title="Statistical Analysis") as tab4:
    gr.Markdown("# 📊 Statistical Analysis")
    gr.Markdown("*Run statistical tests on your data*")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### enter a dict that comply for annova function")
            annova_input = gr.Textbox(label="annova")
            annova_min_sample_input = gr.Textbox(label="min sample size for annova")
            annova_btn = gr.Button("run annova")

            gr.Markdown("### enter a table that comply for tukey function")
            tukey_input = gr.Textbox(label="tukey")
            tukey_min_sample_input = gr.Textbox(label="min sample size for tukey")
            tukey_btn = gr.Button("run tukey")

            gr.Markdown("### Enter a query that comply with the requested embedding format")
            tsne_cluster_input = gr.Textbox(label="embedding_table")
            tsne_cluster_btn = gr.Button("run TSNE")

            gr.Markdown("### Enter a query that comply with the requested embedding centroid format")
            vector_centroid_input = gr.Textbox(label="embedding_table_for_vector")
            vector_centroid_btn = gr.Button("Compute centroid")


        with gr.Column(scale=2):
            annova_output = gr.Textbox(label="annova output")
            tukey_output = gr.Textbox(label="tukey output")
            tsne_output = gr.Textbox(label="tsne_clustering output")
            vector_centroid_output = gr.Textbox(label="Centroid")
    
    # Database operations
    annova_btn.click(do_annova, inputs=[annova_input, annova_min_sample_input], outputs=annova_output)
    tukey_btn.click(do_tukey_test, inputs=[tukey_input, tukey_min_sample_input], outputs=tukey_output)
    tsne_cluster_btn.click(do_tsne_embedding, inputs=tsne_cluster_input, outputs=tsne_output)
    vector_centroid_btn.click(do_vector_centroid, inputs=vector_centroid_input, outputs=vector_centroid_output)

with gr.Blocks(title="MCP guidelines") as tab5:
    gr.Markdown("### 📚 Server Documentation")
    instructions_btn = gr.Button("📖 Get MCP Instructions", variant="secondary")      
    instructions_output = gr.Textbox(label="📚 MCP Server Instructions", lines=15)
    instructions_btn.click(get_mcp_server_instructions, outputs=instructions_output)

with gr.Blocks(title="Application Guide") as tab0:
    gr.Markdown("# 🎯 E-commerce Database Analytics MCP Server")
    gr.Markdown("*Your comprehensive guide to data analysis and business intelligence*")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("""
                ## 🌟 Welcome to Your Data Analytics MCP Server!

                This is a comprehensive e-commerce database analytics MCP Server that combines traditional database operations with cutting-edge AI-powered insights. Whether you're a data analyst, business intelligence professional, or researcher, this MCP server provides everything you need to explore, analyze, and extract insights from e-commerce data.
                        """)
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""
                ## 🎯 What This MCP Server Does
                """)
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""   
                ### 🗄️ **Database Operations**
                - **Explore database structure** (schemas, tables, columns)
                - **Execute safe SQL queries** (read-only for data safety)
                - **Create and manage tables** for analysis
                - **Sample and preview data** before deep analysis

                ### 🤖 **AI-Powered Analytics** 
                - **Natural language to code generation** - Ask questions in plain English
                - **Automated data visualization** - Generate charts and graphs instantly
                - **File management** - Download reports and datasets
                - **Text embedding** - Convert text to vector representations
            """)
        with gr.Column(scale=1):
            gr.Markdown("""
                ### 📊 **Advanced Statistical Analysis**
                - **ANOVA testing** - Compare means across groups
                - **Tukey post-hoc tests** - Identify specific group differences
                - **t-SNE clustering** - Visualize high-dimensional data
                - **Vector analysis** - Calculate centroids and similarities

                ### 📚 **MCP Server Integration**
                - **Complete API documentation** for external clients
                - **Function reference** for all available operations
                - **Integration guidelines** for seamless connectivity
            """)
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""
                ## 🚀 How to Use Our MCP Server
                """)
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""
                ### For Beginners: Start Here!

                1. **🗄️ Go to "Database Operations" tab**
                - Click "Get Schemas" to see available data
                - Explore tables with "Get Tables" 
                - Check table structure with "Get Columns"
                - Run your first query: `SELECT * FROM customers LIMIT 10`

                2. **🤖 Try "AI Analytics" tab**
                - Ask in plain English: "Show me customer demographics"
                - Generate charts by providing data in JSON format
                - Let AI write complex analysis code for you

                3. **📊 Use "Statistical Analysis" tab**
                - Test hypotheses with ANOVA
                - Find group differences with Tukey tests
                - Visualize data patterns with t-SNE
            """)
        with gr.Column(scale=1):
            gr.Markdown("""  
                ### For Advanced Users:
                - **Create custom analysis tables** using SQL queries
                - **Build statistical models** with embedding vectors  
                - **Generate automated reports** through AI integration
                - **Develop MCP client applications** using our API
            """)
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""
                ## 🔧 Main Methods & Functions
                ### 🗄️ Database Discovery
                ```python
                get_schemas()                              # List all database schemas
                get_db_infos()                            # Get database metadata
                get_list_of_tables_in_schema(schema)      # Find tables in schema
                get_list_of_column_in_table(schema, table) # Get column information
                ```

                ### 📊 Data Analysis  
                ```python
                run_read_only_query(sql_query)            # Execute safe SELECT queries
                create_table_from_query(name, query)      # Create tables from analysis
                drop_table(table_name)                    # Remove temporary tables
                ```
                        
                ### 🤖 AI-Powered Functions
                ```python
                generate_code_wrapper(natural_language)   # Convert questions to code
                generate_graph_wrapper(type, data_json)   # Create visualizations
                query_and_generate_graph(query, type)     # Query data + create graph
                embed_text_modal_api(text)                # Convert text to vectors
                ```

                ### 📈 Statistical Methods
                ```python
                do_annova(table, min_sample_size)         # ANOVA statistical test
                do_tukey_test(table, min_sample_size)     # Tukey post-hoc analysis  
                do_tsne_embedding(query)                  # t-SNE clustering
                do_vector_centroid(query)                 # Calculate vector centroids
                ```

                ### 📁 File Operations
                ```python
                download_file_wrapper(file_path)          # Download generated files
                get_mcp_server_instructions()             # Get complete API docs
                ```
            """)
    with gr.Row():
        with gr.Accordion("💡 Common Use Cases & Examples!", open=False):
            gr.Markdown("""
                ### 🛍️ **E-commerce Analysis**
                - **Customer Segmentation**: "Find customer groups by purchase behavior"
                - **Sales Performance**: "Compare revenue across product categories"
                - **Market Analysis**: "Identify trending products and seasonal patterns"

                ### 📊 **Business Intelligence**
                - **KPI Monitoring**: Track key performance indicators
                - **Trend Analysis**: Identify business trends and patterns
                - **Forecasting**: Predict future sales and customer behavior

                ### 🔬 **Research & Analytics**
                - **Hypothesis Testing**: Validate business assumptions with statistics
                - **A/B Testing**: Compare different strategies or products
                - **Data Mining**: Discover hidden patterns in large datasets
            """)
    with gr.Row():
        with gr.Accordion("🎨 Visualization Examples", open=False):
            gr.Markdown("""
                ### Create Charts Instantly:
                ```json
                {
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "values": [150000, 180000, 220000, 195000]
                }
                ```
                **Result**: Beautiful bar/line/pie charts in seconds!

                ### AI-Generated Analysis:
                **Input**: "Analyze customer age distribution by product category"
                **Output**: Complete Python code + statistical analysis + visualizations

                ## ⚡ Quick Start Examples

                ### Example 1: Customer Analysis
                ```sql
                -- Step 1: Explore customer data
                SELECT * FROM customers LIMIT 10;

                -- Step 2: Analyze demographics  
                SELECT age_group, COUNT(*) 
                FROM customers 
                GROUP BY age_group;

                -- Step 3: Create analysis table
                CREATE TABLE age_analysis AS 
                SELECT age_group, AVG(total_spent) as avg_spending
                FROM customers 
                GROUP BY age_group;
                ```

                ### Example 2: AI-Powered Insights
                **Natural Language Request**: 
                "Compare average order values between different customer segments and create a visualization"

                **AI Will Generate**:
                - SQL queries to extract relevant data
                - Statistical analysis of the differences
                - Visualization code for clear presentation
                - Interpretation of the results

                """)
    with gr.Row():
        with gr.Accordion("🛡️ Safety Features", open=False):
            gr.Markdown("""
                - **Read-Only Queries**: Data exploration without modification risk
                - **Core Table Protection**: System tables cannot be accidentally deleted
                - **Error Handling**: Clear feedback for all operations
                - **Transaction Safety**: Automatic rollback on errors
            """)
    with gr.Row():
        with gr.Accordion("🎯 Best Practices", open=False):
            gr.Markdown("""
                1. **Start with Discovery**: Always explore data structure first
                2. **Sample Before Analyzing**: Check data quality with small samples
                3. **Use Descriptive Names**: Name analysis tables clearly
                4. **Leverage AI**: Use natural language for complex analysis
                5. **Clean Up**: Remove temporary tables when finished
                6. **Check Results**: Verify outputs before making decisions
            """)
    with gr.Row():
        with gr.Accordion("🚀 Ready to Begin?", open=False):
            gr.Markdown("""
                ### Choose your starting point:                 
                - **New to the this MCP Server?** → Start with "Database Operations" 
                - **Want AI help?** → Jump to "AI Analytics"
                - **Need statistics?** → Go to "Statistical Analysis"  
                - **Building integrations?** → Check "MCP Guidelines"

                **Let's turn your data into insights! 📈✨**
                        """)

# Create the TabbedInterface
interface = gr.TabbedInterface(
    [tab0, tab0, tab1, tab2, tab4, tab5], 
    tab_names=["🔌 Database Setup", "🎯 Guide", "🗄️ Database Operations", "🤖 AI Analytics", "📊 Statistical Analysis", "📊 MCP guidelines"],
    title="E-commerce Database Analytics MCP Server",
    theme=gr.themes.Soft()
)

# Launch the app
if __name__ == "__main__":
    print("🚀 Starting E-commerce Database Analytics MCP Server...")
    print(f"🌐 Dashboard: http://localhost:7860")
    print("🔗 Integrated with FastAPI service for AI analytics")
    
    interface.launch(server_name="0.0.0.0", server_port=7860, share=True, mcp_server=True)