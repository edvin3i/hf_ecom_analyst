import gradio as gr

# Define the functions
def discover_db(input_text):
    return f"Discovered from DB: {input_text}"

def query_db(query):
    return f"Query result: {query}"

def get_analytics(param):
    return f"Analytics data: {param}"

# Create the Gradio Blocks interface
with gr.Blocks() as interface:
    with gr.Row():
        with gr.Column(scale=1):
            discover_input = gr.Textbox(label="Discover DB Input")
            discover_btn = gr.Button("Run Discover DB")
            
            query_input = gr.Textbox(label="Query DB Input")
            query_btn = gr.Button("Run Query DB")
            
            analytics_input = gr.Textbox(label="Get Analytics Input")
            analytics_btn = gr.Button("Run Get Analytics")
        
        with gr.Column(scale=2):
            discover_output = gr.Textbox(label="Discover DB Output")
            query_output = gr.Textbox(label="Query DB Output")
            analytics_output = gr.Textbox(label="Analytics Output")

    # Bind functions to buttons
    discover_btn.click(discover_db, inputs=discover_input, outputs=discover_output)
    query_btn.click(query_db, inputs=query_input, outputs=query_output)
    analytics_btn.click(get_analytics, inputs=analytics_input, outputs=analytics_output)

# Launch the app
interface.launch(mcp_server=True)

