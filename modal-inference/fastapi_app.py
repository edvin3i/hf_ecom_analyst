import modal
import os


image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "openai==1.84.0",
    "langchain==0.3.25",
    "langchain_openai==0.3.19",
    "langchain_experimental==0.3.4",
    "matplotlib==3.10.3",
    "Pillow==10.4.0",
    "fastapi[standard]",
    "boto3",
    "pydantic",
)

app = modal.App(
    name="example-fastapi",
    image=image,
    secrets=[modal.Secret.from_name("gemini-secret")],
)

agent_executor = None  # Global variable to hold the agent executor

@app.function(image=image, secrets=[modal.Secret.from_name("gemini-secret")], volumes={"/my_vol": modal.Volume.from_name("my-volume")})
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    import asyncio
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import FileResponse
    from concurrent.futures import ThreadPoolExecutor
    from pydantic import BaseModel
    from langchain_experimental.agents import agent_toolkits
    from langchain_experimental.tools import PythonREPLTool
    from langchain.agents import AgentType
    from langchain_openai import ChatOpenAI
    import tempfile
    import os
    import uuid


    executor = ThreadPoolExecutor()
    web_app = FastAPI()
    
    global agent_executor
    if agent_executor is None:
        api_key = os.environ["GEMINI_API_KEY"]
        
        # List of models to try, in order of preference
        models = [
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-experimental",
            "gemini-1.5-flash",
        ]
        
        initialized_successfully = False
        for model_name in models:
            try:
                print(f"Attempting to initialize agent with model: {model_name}")
                agent_executor = agent_toolkits.create_python_agent(
                    llm=ChatOpenAI(temperature=0, model=model_name,
                                   openai_api_key=api_key, 
                                   base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
                    tool=PythonREPLTool(),
                    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                    agent_executor_kwargs={"handle_parsing_errors": True},
                )
                print(f"Successfully initialized agent with model: {model_name}")
                initialized_successfully = True
                break  # Exit loop if initialization is successful
            except Exception as e:
                print(f"Failed to initialize agent with model {model_name}: {e}")
                agent_executor = None # Ensure agent_executor is None if this attempt fails
                # Continue to the next model in the list
        
        if not initialized_successfully:
            # This part will be executed if all models fail.
            # You might want to raise an HTTPException or log a critical error.
            print("Failed to initialize agent with any of the available models.")
            # For a FastAPI app, you might want to prevent startup or set a status
            # indicating the service is degraded. For now, we'll let it proceed,
            # but endpoints relying on agent_executor will fail if it's None.
            # Consider raising a more specific error or handling this state.
            raise RuntimeError("Could not initialize the agent with any available LLM models.")


    class CodeRequest(BaseModel):
        user_request: str

    class CodeResponse(BaseModel):
        output: str

    class GraphRequest(BaseModel):
        graph_type: str
        data: str  # JSON formatted string containing the data for visualization
        
        class Config:
            json_schema_extra = {
                "example": {
                    "graph_type": "bar",
                    "data": '{"labels": ["A", "B", "C"], "values": [1, 2, 3]}'
                }
            }

    class GraphResponse(BaseModel):
        message: str
        image_path: str

    @web_app.get("/health")
    async def healthCheck():
        return {"status": "ok"}

    @web_app.post("/generate-code", response_model=CodeResponse)
    async def generateAndRunPythonCode(request: CodeRequest):
        """
        Generate and run python code using langchain
        """
        response = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: agent_executor.invoke({"input": request.user_request})
        )
        return CodeResponse(output=response["output"])

    @web_app.post("/generate-graph")
    async def generateGraph(request: GraphRequest):
        """
        Generate a graph through matplotlib using langchain agent with specified graph type and data
        
        Args:
            request: GraphRequest containing:
                - graph_type: Type of graph (e.g., "bar", "line", "pie", "scatter")
                - data: JSON formatted string with the data structure for the graph
                  Examples:
                  - Bar/Line: '{"labels": ["A", "B", "C"], "values": [1, 2, 3]}'
                  - Pie: '{"labels": ["Category1", "Category2"], "values": [30, 70]}'
                  - Scatter: '{"x": [1, 2, 3, 4], "y": [10, 20, 25, 30]}'
        
        Returns:
            FileResponse with the generated graph image
        """
        import json
        
        # Validate JSON format
        try:
            json.loads(request.data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Data must be valid JSON format")
        
        # Create a unique filename for the graph
        graph_filename = f"graph_{uuid.uuid4().hex}.png"
        graph_path = f"/my_vol/{graph_filename}"
        
        # Construct the prompt for the agent
        prompt = f"""
        Create a {request.graph_type} graph using the following JSON data: {request.data}
        Parse the JSON data and use matplotlib to create the graph and save it to {graph_path}
        Make sure the graph is properly formatted with labels, title, and legend if needed.
        The data is in JSON format, so parse it appropriately for the {request.graph_type} chart type.
        Return the absolute path of the saved image file.
        """
        
        response = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: agent_executor.invoke({"input": prompt})
        )
        
        # Check if file was created successfully
        if not os.path.exists(graph_path):
            raise HTTPException(status_code=500, detail="Failed to generate graph file")
        
        return FileResponse(
            path=graph_path,
            filename=graph_filename,
            media_type='image/png'
        )

    @web_app.get("/download-file")
    async def downloadFile(file_path: str):
        """
        Download a file by its path from the volume storage
        """
        # Security check: ensure the file path is within the volume directory
        if not file_path.startswith("/my_vol/"):
            raise HTTPException(status_code=400, detail="Invalid file path. Must be within /my_vol/ directory")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Extract filename for the download
        filename = os.path.basename(file_path)
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )

    return web_app
