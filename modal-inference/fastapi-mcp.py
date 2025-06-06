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
    "fastapi-mcp"
)

app = modal.App(
    name="example-fastapi",
    image=image,
    secrets=[modal.Secret.from_name("gemini-secret")],
)


@app.function(image=image)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, Request
    from fastapi_mcp import FastApiMCP

    web_app = FastAPI()


    @web_app.post("/echo")
    async def echo(request: Request):
        body = await request.json()
        return body
    
    @web_app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    mcp = FastApiMCP(web_app)
    mcp.mount()

    return web_app