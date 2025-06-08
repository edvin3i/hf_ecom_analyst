# ---
# cmd: ["modal", "run", "06_gpu_and_ml/embeddings/text_embeddings_inference.py::embed_dataset"]
# ---

# # Run TextEmbeddingsInference (TEI) on Modal

# This example runs the [Text Embedding Inference (TEI)](https://github.com/huggingface/text-embeddings-inference) toolkit on the Hacker News BigQuery public dataset.

import json
import os
import socket
import subprocess
from pathlib import Path

import modal

GPU_CONFIG = "A10G"
MODEL_ID = "BAAI/bge-base-en-v1.5"
DOCKER_IMAGE = (
    "ghcr.io/huggingface/text-embeddings-inference:86-0.4.0"  # Ampere 86 for A10s.
    # "ghcr.io/huggingface/text-embeddings-inference:0.4.0" # Ampere 80 for A100s.
    # "ghcr.io/huggingface/text-embeddings-inference:0.3.0"  # Turing for T4s.
)

DATA_PATH = Path("/data/dataset.jsonl")

LAUNCH_FLAGS = [
    "--model-id",
    MODEL_ID,
    "--port",
    "8000",
]


def spawn_server() -> subprocess.Popen:
    process = subprocess.Popen(["text-embeddings-router"] + LAUNCH_FLAGS)

    # Poll until webserver at 127.0.0.1:8000 accepts connections before running inputs.
    while True:
        try:
            socket.create_connection(("127.0.0.1", 8000), timeout=1).close()
            print("Webserver ready!")
            return process
        except (socket.timeout, ConnectionRefusedError):
            # Check if launcher webserving process has exited.
            # If so, a connection can never be made.
            retcode = process.poll()
            if retcode is not None:
                raise RuntimeError(f"launcher exited unexpectedly with code {retcode}")


def download_model():
    # Wait for server to start. This downloads the model weights when not present.
    spawn_server().terminate()


app = modal.App("embeddings-api")

tei_image = (
    modal.Image.from_registry(
        DOCKER_IMAGE,
        add_python="3.10",
    )
    .dockerfile_commands("ENTRYPOINT []")
    .run_function(download_model, gpu=GPU_CONFIG)
    .pip_install("httpx", "fastapi[standard]", "numpy")
)

# Global variable to hold the TEI client
tei_client = None


@app.function(
    gpu=GPU_CONFIG,
    image=tei_image,
    max_containers=4,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    import asyncio
    import numpy as np
    from fastapi import FastAPI, HTTPException
    from httpx import AsyncClient
    from pydantic import BaseModel
    from typing import List, Union, Optional
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor()
    web_app = FastAPI()

    global tei_client
    if tei_client is None:
        # Start TEI server
        process = spawn_server()
        tei_client = AsyncClient(base_url="http://127.0.0.1:8000")

    class EmbedRequest(BaseModel):
        texts: List[str]

    class EmbedResponse(BaseModel):
        embeddings: List[List[float]]

    class SimilarityRequest(BaseModel):
        text1: Optional[str] = None
        text2: Optional[str] = None
        vector1: Optional[List[float]] = None
        vector2: Optional[List[float]] = None

    class SimilarityResponse(BaseModel):
        similarity: float

    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    @web_app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            # Test if TEI server is responsive
            resp = await tei_client.get("/health")
            if resp.status_code == 200:
                return {"status": "ok", "model": MODEL_ID}
            else:
                return {"status": "degraded", "model": MODEL_ID}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @web_app.post("/embed", response_model=EmbedResponse)
    async def embed_texts(request: EmbedRequest):
        """
        Generate embeddings for the provided texts
        """
        try:
            resp = await tei_client.post("/embed", json={"inputs": request.texts})
            resp.raise_for_status()
            embeddings = resp.json()

            return EmbedResponse(embeddings=embeddings)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

    @web_app.post("/similarity", response_model=SimilarityResponse)
    async def calculate_similarity(request: SimilarityRequest):
        """
        Calculate cosine similarity between two texts or vectors
        """
        try:
            # Case 1: Both texts provided
            if request.text1 is not None and request.text2 is not None:
                # Get embeddings for both texts
                resp = await tei_client.post("/embed", json={"inputs": [request.text1, request.text2]})
                resp.raise_for_status()
                embeddings = resp.json()

                if len(embeddings) != 2:
                    raise HTTPException(status_code=500, detail="Failed to get embeddings for both texts")

                vector1, vector2 = embeddings[0], embeddings[1]

            # Case 2: Both vectors provided
            elif request.vector1 is not None and request.vector2 is not None:
                vector1, vector2 = request.vector1, request.vector2

                if len(vector1) != len(vector2):
                    raise HTTPException(status_code=400, detail="Vectors must have the same dimension")

            # Case 3: Invalid input
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either provide both text1 and text2, or both vector1 and vector2"
                )

            # Calculate cosine similarity
            similarity = cosine_similarity(vector1, vector2)

            return SimilarityResponse(similarity=similarity)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to calculate similarity: {str(e)}")

    return web_app


# def download_data():
#     service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
#     credentials = service_account.Credentials.from_service_account_info(
#         service_account_info
#     )

#     client = bigquery.Client(credentials=credentials)

#     iterator = client.list_rows(
#         "bigquery-public-data.hacker_news.full",
#         max_results=100_000,
#     )
#     df = iterator.to_dataframe(progress_bar_type="tqdm").dropna()

#     df["id"] = df["id"].astype(int)
#     df["text"] = df["text"].apply(lambda x: x[:512])

#     data = list(zip(df["id"], df["text"]))

#     with open(DATA_PATH, "w") as f:
#         json.dump(data, f)

#     volume.commit()


# image = modal.Image.debian_slim(python_version="3.10").pip_install(
#     "google-cloud-bigquery", "pandas", "db-dtypes", "tqdm"
# )

# with image.imports():
#     from google.cloud import bigquery
#     from google.oauth2 import service_account


# @app.function(
#     image=image,
#     secrets=[modal.Secret.from_name("bigquery")],
#     volumes={DATA_PATH.parent: volume},
# )
# def embed_dataset():
#     model = TextEmbeddingsInference()

#     if not DATA_PATH.exists():
#         print("Downloading data. This takes a while...")
#         download_data()

#     with open(DATA_PATH) as f:
#         data = json.loads(f.read())

#     def generate_batches():
#         batch = []
#         for item in data:
#             batch.append(item)

#             if len(batch) == BATCH_SIZE:
#                 yield batch
#                 batch = []

#     # data is of type list[tuple[str, str]].
#     # starmap spreads the tuples into positional arguments.
#     for output_batch in model.embed.map(generate_batches(), order_outputs=False):
#         # Do something with the outputs.
#         pass
