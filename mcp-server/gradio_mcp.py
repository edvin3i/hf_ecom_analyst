import ast
import gradio as gr
from db_work import DatabaseInterface
import os
from PIL import Image
import var_stats

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



    # Bind functions to buttons
    discover_btn.click(get_schemas, outputs=schema_info)
    database_info_btn.click(get_db_infos, outputs=db_info)
    table_in_schema_btn.click(get_list_of_tables_in_schema, inputs=table_in_schema_input, outputs=table_in_schema)
    column_btn.click(get_list_of_column_in_table, inputs=[schema_input, table_input], outputs=column_output)
    query_btn.click(run_read_only_query, inputs=query_input, outputs=query_output)
    annova_btn.click(do_annova, inputs=[annova_input, annova_min_sample_input], outputs=annova_output)
    tukey_btn.click(do_tukey_test, inputs=[tukey_input, tukey_min_sample_input], outputs=tukey_output)

# Launch the app
interface.launch(mcp_server=True, share=True)

