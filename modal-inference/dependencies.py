from pathlib import Path

import modal
import os


image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "openai==1.84.0",
    "langchain==0.3.25",
    "langchain_openai==0.3.19",
    "langchain_experimental==0.3.4",
)

app = modal.App(
    name="example-google-genai",
    image=image,
    secrets=[modal.Secret.from_name("gemini-secret")],
)


@app.function(secrets=[modal.Secret.from_name("gemini-secret")])
def generate_simle_response(text: str):
    """
    Generate a simple response using Google Gemini API.
    """
    from openai import OpenAI
    
    api_key=os.environ["GEMINI_API_KEY"]
    model="gemini-1.5-flash"
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": text
            }
        ]
    )
    return response.choices[0].message

@app.function(secrets=[modal.Secret.from_name("gemini-secret")])
def generate_code(user_request: str):
    """
    Generate code using langchain
    """
    from langchain_experimental.agents import agent_toolkits
    from langchain_experimental.tools import PythonREPLTool
    from langchain.agents import AgentType
    from langchain_openai import ChatOpenAI

    api_key=os.environ["GEMINI_API_KEY"]
    model="gemini-2.0-flash"
    
    agent_executor = agent_toolkits.create_python_agent(
        llm=ChatOpenAI(temperature=0, model=model, 
                       openai_api_key=os.environ["GEMINI_API_KEY"],base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
        tool=PythonREPLTool(),
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_executor_kwargs={"handle_parsing_errors": True}
    )
    response = agent_executor.invoke({"input": user_request})
    return response["output"]



@app.local_entrypoint()
def main():
    print("Running locally")
    sample_text = "Hello! Can you tell me about artificial intelligence?"
    # result = inference.remote(sample_text)
    # print(f"Gemini response: {result.content}")
    
    sample_calculation = "Calculate 3^4 + math.sqrt(81)"
    result = generate_code.remote(sample_calculation)
    print(f"Gemini calculation: {result}")
    print("Done")
