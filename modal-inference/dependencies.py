from pathlib import Path

import modal
import os


image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "google-genai==1.19.0"
)

app = modal.App(
    name="example-google-genai",
    image=image,
    secrets=[modal.Secret.from_name("gemini-secret")],
)


@app.function(secrets=[modal.Secret.from_name("gemini-secret")])
def inference(text: str):
    from google import genai
    
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=text
    )
    
    return response.text


@app.local_entrypoint()
def main():
    print("Running locally")
    sample_text = "Hello! Can you tell me about artificial intelligence?"
    result = inference.remote(sample_text)
    print(f"Gemini response: {result}")
    print("Done")
