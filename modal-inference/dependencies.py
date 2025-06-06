from pathlib import Path

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

    api_key = os.environ["GEMINI_API_KEY"]
    model = "gemini-1.5-flash"
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


@app.function(secrets=[modal.Secret.from_name("gemini-secret")], volumes={"/my_vol": modal.Volume.from_name("my-volume")})
def generate_code(user_request: str):
    """
    Generate code using langchain
    """
    from langchain_experimental.agents import agent_toolkits
    from langchain_experimental.tools import PythonREPLTool
    from langchain.agents import AgentType
    from langchain_openai import ChatOpenAI
    # from typing import Any, Dict, Optional

    # from langchain.agents.agent import AgentExecutor, BaseSingleActionAgent
    # from langchain.agents.mrkl.base import ZeroShotAgent
    # from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
    # from langchain.agents.types import AgentType
    # from langchain.chains.llm import LLMChain
    # from langchain_core.callbacks.base import BaseCallbackManager
    # from langchain_core.language_models import BaseLanguageModel
    # from langchain_core.messages import SystemMessage

    # from langchain_experimental.agents.agent_toolkits.python.prompt import PREFIX
    # from langchain_experimental.tools.python.tool import PythonREPLTool

    api_key = os.environ["GEMINI_API_KEY"]
    model = "gemini-2.0-flash"

    # def ft_create_python_agent(
    #     llm: BaseLanguageModel,
    #     tools: list,
    #     agent_type: AgentType = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    #     callback_manager: Optional[BaseCallbackManager] = None,
    #     verbose: bool = False,
    #     prefix: str = PREFIX,
    #     agent_executor_kwargs: Optional[Dict[str, Any]] = None,
    #     **kwargs: Dict[str, Any],
    # ) -> AgentExecutor:
    #     """Construct a python agent from an LLM and tool."""
    #     tools = tools
    #     agent: BaseSingleActionAgent

    #     if agent_type == AgentType.ZERO_SHOT_REACT_DESCRIPTION:
    #         prompt = ZeroShotAgent.create_prompt(tools, prefix=prefix)
    #         llm_chain = LLMChain(
    #             llm=llm,
    #             prompt=prompt,
    #             callback_manager=callback_manager,
    #         )
    #         tool_names = [tool.name for tool in tools]
    #         agent = ZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names, **kwargs)  # type: ignore[arg-type]
    #     elif agent_type == AgentType.OPENAI_FUNCTIONS:
    #         system_message = SystemMessage(content=prefix)
    #         _prompt = OpenAIFunctionsAgent.create_prompt(system_message=system_message)
    #         agent = OpenAIFunctionsAgent(  # type: ignore[call-arg]
    #             llm=llm,
    #             prompt=_prompt,
    #             tools=tools,
    #             callback_manager=callback_manager,
    #             **kwargs,  # type: ignore[arg-type]
    #         )
    #     else:
    #         raise ValueError(f"Agent type {agent_type} not supported at the moment.")
    #     return AgentExecutor.from_agent_and_tools(
    #         agent=agent,
    #         tools=tools,
    #         callback_manager=callback_manager,
    #         verbose=verbose,
    #         **(agent_executor_kwargs or {}),
    #     )

    agent_executor = agent_toolkits.create_python_agent(
        llm=ChatOpenAI(temperature=0, model=model,
                       openai_api_key=os.environ["GEMINI_API_KEY"], base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
        tool=PythonREPLTool(),
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_executor_kwargs={"handle_parsing_errors": True},
    )
    response = agent_executor.invoke({"input": user_request})
    return response["output"]


def is_valid_base64(s: str) -> bool:
    """
    Check if a string is valid base64 encoded.
    """
    import base64
    import re

    # Handle bytes object representation
    if s.startswith("b'") and s.endswith("'"):
        s = s[2:-1]  # Remove b' and '

    # Remove data URL prefix if present (e.g., "data:image/png;base64,")
    if s.startswith('data:'):
        s = s.split(',', 1)[1] if ',' in s else s

    # Check if string contains only valid base64 characters
    if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', s):
        return False

    try:
        # Try to decode the string
        decoded = base64.b64decode(s, validate=True)
        return len(decoded) > 0
    except Exception:
        return False


def save_base64_image(base64_string: str, output_path: str) -> bool:
    """
    Convert base64 string to image and save it.
    Returns True if successful, False otherwise.
    """
    import base64
    from PIL import Image
    from io import BytesIO

    try:
        # Handle bytes object representation
        if base64_string.startswith("b'") and base64_string.endswith("'"):
            base64_string = base64_string[2:-1]  # Remove b' and '

        # Remove data URL prefix if present
        if base64_string.startswith('data:'):
            base64_string = base64_string.split(',', 1)[1]

        # Decode base64 string
        image_data = base64.b64decode(base64_string)

        # Convert to PIL Image
        image = Image.open(BytesIO(image_data))

        # Save image
        image.save(output_path)
        print(f"Image saved successfully to: {output_path}")
        return True

    except Exception as e:
        print(f"Error saving image: {e}")
        return False


@app.local_entrypoint()
def main():
    print("Running locally")
    sample_text = "Hello! Can you tell me about artificial intelligence?"
    # result = inference.remote(sample_text)
    # print(f"Gemini response: {result.content}")

    sample_calculation = "Build a graph for function y=x^2 using matplotlib than save image of graph in /my_vol. Return absolute ddress of saved image"
    result = generate_code.remote(sample_calculation)
    print(f"Gemini calculation: {result}")

    # Check if result contains valid base64 and save as image
    # if is_valid_base64(result):
    #     print("Valid base64 string detected")
    #     output_path = "/home/tphung/projects/hf_ecom_analyst/generated_graph.png"
    #     if save_base64_image(result, output_path):
    #         print("Graph saved successfully!")
    #     else:
    #         print("Failed to save the graph")
    # else:
    #     print("Result is not a valid base64 string")
    #     print("Raw result:", result[:200] +
    #           "..." if len(result) > 200 else result)

    print("Done")
