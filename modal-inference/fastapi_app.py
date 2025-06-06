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
    from fastapi import FastAPI, Request
    from concurrent.futures import ThreadPoolExecutor
    from pydantic import BaseModel
    from langchain_experimental.agents import agent_toolkits
    from langchain_experimental.tools import PythonREPLTool
    from langchain.agents import AgentType
    from langchain_openai import ChatOpenAI


    executor = ThreadPoolExecutor()
    web_app = FastAPI()
    
    global agent_executor
    if agent_executor is None:
        api_key = os.environ["GEMINI_API_KEY"]
        model = "gemini-2.0-flash"

        agent_executor = agent_toolkits.create_python_agent(
            llm=ChatOpenAI(temperature=0, model=model,
                           openai_api_key=api_key, 
                           base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
            tool=PythonREPLTool(),
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            agent_executor_kwargs={"handle_parsing_errors": True},
        )

    class CodeRequest(BaseModel):
        user_request: str

    class CodeResponse(BaseModel):
        output: str

    @web_app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @web_app.post("/generate-code", response_model=CodeResponse)
    async def generate_code_endpoint(request: CodeRequest):
        """
        Generate code using langchain
        """
        response = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: agent_executor.invoke({"input": request.user_request})
        )
        return CodeResponse(output=response["output"])

    return web_app
