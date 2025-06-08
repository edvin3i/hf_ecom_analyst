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
    """### `get_schemas()`
            - **Purpose**: Retrieve all database schemas
            - **Returns**: JSON object containing schema information
            - **Use Case**: Initial database exploration"""
    return db_interface.list_schemas()

def get_db_infos():
    """### `get_db_infos()`
            - **Purpose**: Get comprehensive database information and metadata
            - **Returns**: JSON object containing database information
            - **Use Case**: Initial database exploration"""
    return db_interface.list_database_info()

def get_list_of_tables_in_schema(schema):
    """### `get_list_of_tables_in_schema(schema_name: str)`
            - **Purpose**: List all tables within a specific schema
            - **Parameters**: `schema_name` - Name of the schema to explore
            - **Returns**: JSON object containing table information
            - **Use Case**: Initial database exploration"""
    return db_interface.list_tables_in_schema(schema)

def get_list_of_column_in_table(schema, table):
    """### `get_list_of_column_in_table(schema_name: str, table_name: str)`
            - **Purpose**: Get detailed column information for a specific table
            - **Parameters**: `schema_name` - Name of the schema containing the table
            - **Returns**: JSON object containing column information
            - **Use Case**: Initial database exploration"""
    return db_interface.list_columns_in_table(schema, table)

def run_read_only_query(query: str):
    """### `run_read_only_query(query: str)`
            - **Purpose**: Execute read-only SQL queries safely
            - **Parameters**: `query` - SQL SELECT statement
            - **Returns**: Query results as rows
            - **Use Case**: Initial database exploration"""
    return db_interface.read_only_query(query)

def create_table_from_query(table_name: str, source_query: str):
    """### `create_table_from_query(table_name: str, source_query: str)`
            - **Purpose**: Create permanent tables from SELECT queries
            - **Parameters**: `table_name` - Name of the new table
            - **Returns**: Status message indicating success or failure
            - **Use Case**: Create analysis datasets from queries"""
    return db_interface.create_table_from_query(table_name, source_query)

def drop_table(table_name: str):
    """### `drop_table(table_name: str)`
            - **Purpose**: Remove tables from the database
            - **Parameters**: `table_name` - Name of the table to drop
            - **Returns**: Status message indicating success or failure
            - **Use Case**: Clean up analysis tables"""
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

def generate_code_wrapper(user_request: str):
    """### `generate_code_wrapper(user_request: str)`
            - **Purpose**: Generate Python code based on user request
            - **Parameters**: `user_request` - Textual description of the analysis
            - **Returns**: Generated code and status message
            - **Use Case**: AI-powered code generation for data analysis"""
    if not user_request.strip():
        return "❌ Please provide a request", ""
    
    output, status = api_service.generate_code(user_request)
    return output or "No output generated", status

def generate_graph_wrapper(graph_type: str, data_json: str):
    """### `generate_graph_wrapper(graph_type: str, data_json: str)`
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

def download_file_wrapper(file_path: str):
    """### `download_file_wrapper(file_path: str)`
            - **Purpose**: Download files from the service
            - **Use Case**: Retrieving generated reports or datasets"""
    if not file_path.strip():
        return "❌ Please provide a file path"
    
    local_path, status = api_service.download_file(file_path)
    return status

# def create_analytics_views_from_file():
#     """### `create_analytics_views_from_file()`
#             - **Purpose**: Create predefined analytics views from SQL file
#             - **Returns**: Status of view creation process
#             - **Use Case**: Setting up standard business intelligence views"""
#     try:
#         result = db_interface.create_analytics_views()
#         return result
#     except Exception as e:
#         return f"❌ Error creating views: {str(e)}"

# def get_all_views():
#     try:
#         views = db_interface.list_views_detailed()
#         if not views:
#             return "No views found in database"
        
#         result = []
#         for view in views:
#             schema, name, owner, definition = view
#             short_def = (definition[:100] + "...") if len(definition) > 100 else definition
#             result.append(f"📋 {schema}.{name} (Owner: {owner})\n   {short_def}\n")
        
#         return "\n".join(result)
#     except Exception as e:
#         return f"❌ Error listing views: {str(e)}"

# def get_view_content_sample(view_name: str, limit_str: str = "10"):
#     if not view_name.strip():
#         return "❌ Please provide a view name"
    
#     try:
#         limit = int(limit_str) if limit_str.strip() else 10
#         limit = min(max(limit, 1), 1000)
        
#         content = db_interface.get_view_content(view_name, limit)
#         if isinstance(content, str):
#             return content
        
#         if not content:
#             return f"View '{view_name}' exists but contains no data"
        
#         result = [f"📊 Sample data from view '{view_name}' (showing {len(content)} rows):\n"]
#         for i, row in enumerate(content[:limit], 1):
#             result.append(f"Row {i}: {row}")
        
#         return "\n".join(result)
#     except ValueError:
#         return "❌ Invalid limit value - please enter a number"
#     except Exception as e:
#         return f"❌ Error getting view content: {str(e)}"

# def delete_view(view_name: str):
#     if not view_name.strip():
#         return "❌ Please provide a view name"
#     return db_interface.drop_view(view_name)

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

            gr.Markdown("### 🔍 Create Table")
            table_name_input = gr.Textbox(label="Table Name", placeholder="table")
            source_query_input = gr.Textbox(label="Source Query", lines=3, placeholder="SELECT * FROM customers LIMIT 10")
            create_table_from_query_btn = gr.Button("Create Table", variant="primary")

            gr.Markdown("### 🔍 Drop Table")
            drop_table_name_input = gr.Textbox(label="Table Name", placeholder="table")
            drop_table_btn = gr.Button("Drop Table", variant="primary")
            
            gr.Markdown("### 🎨 Sample Visualization")
            generate_sample_btn = gr.Button("Generate Sample", variant="secondary")
            
        with gr.Column(scale=2):
            schema_info = gr.Textbox(label="📋 Schema Information", lines=5)
            db_info = gr.Textbox(label="ℹ️ Database Information", lines=5)
            table_in_schema = gr.Textbox(label="📊 Tables in Schema", lines=5)
            column_output = gr.Textbox(label="📄 Table Columns", lines=5)
            query_output = gr.Textbox(label="🔍 Query Results", lines=8)
            table_status = gr.Textbox(label="table status")
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
        with gr.Column(scale=2):
            views_creation_output = gr.Textbox(
                label="📈 Views Creation Status", 
                lines=5,
                info="Status of analytics views creation"
            )
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📋 View Browser")
            refresh_views_btn = gr.Button("🔄 Refresh View List", variant="secondary")
        with gr.Column(scale=2):
                views_list_output = gr.Textbox(
                label="📋 Available Views", 
                lines=10,
                info="List of all database views"
            )
                
    with gr.Row():
        with gr.Column(scale=1):
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
        with gr.Column(scale=2):
                view_content_output = gr.Textbox(
                label="🔍 View Content", 
                lines=10,
                info="Sample data from selected view"
            )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🗑️ View Management")
            delete_view_name = gr.Textbox(label="View Name to Delete", placeholder="view_to_delete")
            delete_view_btn = gr.Button("🗑️ Delete View", variant="stop")
        with gr.Column(scale=2):
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

# TAB 4: Statistical Analysis
    with gr.Blocks(title="Statistical Analysis") as tab4:
        gr.Markdown("# 📊 Statistical Analysis")
        gr.Markdown("*Run statistical tests on your data*")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### enter a dict that comply to annova function")
                annova_input = gr.Textbox(label="annova")
                annova_min_sample_input = gr.Textbox(label="min sample size for annova")
                annova_btn = gr.Button("run annova")

                gr.Markdown("### enter a dict that comply to tukey function")
                tukey_input = gr.Textbox(label="tukey")
                tukey_min_sample_input = gr.Textbox(label="min sample size for tukey")
                tukey_btn = gr.Button("run tukey")


            with gr.Column(scale=2):
                annova_output = gr.Textbox(label="annova output")
                tukey_output = gr.Textbox(label="tukey output")

    # FIXED: Proper function bindings with correct inputs/outputs
    
    # Database operations
    annova_btn.click(do_annova, inputs=[annova_input, annova_min_sample_input], outputs=annova_output)
    tukey_btn.click(do_tukey_test, inputs=[tukey_input, tukey_min_sample_input], outputs=tukey_output)

    # TAB 5: MCP guidelines
    with gr.Blocks(title="MCP Guidelines") as tab5:
        gr.Markdown("# 📚 MCP Client Guidelines")
        gr.Markdown("*Complete documentation for MCP clients using this analytics server*")
    with gr.Column():
        gr.Markdown("""
            ## Purpose
            This MCP server provides comprehensive e-commerce database analytics capabilities, enabling clients to explore database schemas, run queries, create views, perform statistical analysis, and generate AI-powered insights. The server is designed to help users analyze customer behavior, sales patterns, and business metrics from e-commerce data.

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
                    
            ### 3. View Management Workflow
            create_analytics_views_from_file() → Setup standard views
            get_all_views() → Discover available views
            get_view_content_sample() → Preview view data
            Use views in queries for analysis
            
            ### 4. AI-Assisted Analysis
            generate_code_wrapper("Analyze customer segments") → Get AI insights
            Use results to guide further manual analysis
            generate_graph_wrapper() → Visualize AI findings
                                 
            ## ✅ Best Practices for MCP Clients
            1. **Start with Discovery**: Always begin by exploring schemas and tables before analysis
            2. **Use Read-Only Queries**: Prefer `run_read_only_query()` for exploration to maintain data safety
            3. **Leverage Views**: Use `get_all_views()` to find pre-built analytics before creating custom queries
            4. **Statistical Validation**: Use `do_annova()` before `do_tukey_test()` for proper statistical workflow
            5. **AI Enhancement**: Use `generate_code_wrapper()` for complex analysis that would be difficult to code manually
            6. **Clean Up**: Use `drop_table()` to remove temporary analysis tables when done
            7. **Error Handling**: All functions return status indicators - check for errors before proceeding
            8. **Data Safety**: Core tables (transactions, customers, articles) are protected from modification

            ## 🎯 Use Cases
            This MCP server is designed for:
            - **E-commerce Analytics**: Customer behavior, sales patterns, product performance
            - **Business Intelligence**: KPI tracking, trend analysis, forecasting
            - **Statistical Research**: Hypothesis testing, comparative analysis
            - **Data Exploration**: Schema discovery, data profiling, relationship analysis
            - **AI-Assisted Insights**: Natural language to analysis, automated reporting""")

# Create the TabbedInterface
interface = gr.TabbedInterface(
    [tab1, tab2, tab3, tab4, tab5], 
    tab_names=["🗄️ Database Operations", "🤖 AI Analytics", "📊 View Management", "📊 Statistical Analysis", "📊 MCP guidelines"],
    title="E-commerce Database Analytics Platform",
    theme=gr.themes.Soft()
)

# Launch the app
if __name__ == "__main__":
    print("🚀 Starting E-commerce Database Analytics Platform...")
    print(f"🌐 Dashboard: http://localhost:7860")
    print("🔗 Integrated with FastAPI service for AI analytics")
    
    interface.launch(server_name="0.0.0.0", server_port=7860, share=True, mcp_server=True)