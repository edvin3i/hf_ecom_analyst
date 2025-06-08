# ---
# cmd: ["modal", "run", "embeddings_deploy.py::fastapi_app"]
# ---

# # Run SentenceTransformers Embeddings on Modal

# This example runs SentenceTransformers for text embeddings on Modal.

import json
import os
from pathlib import Path
from typing import List, Optional

import modal

GPU_CONFIG = "A10G"
MODEL_ID = "sentence-transformers/clip-ViT-L-14"

app = modal.App("embeddings-api")

# Create image with SentenceTransformers
def download_model():
    from sentence_transformers import SentenceTransformer
    # Download and cache the model
    model = SentenceTransformer(MODEL_ID)
    print(f"Model {MODEL_ID} downloaded successfully")

embeddings_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("sentence-transformers", "fastapi[standard]", "torch", "numpy", "pillow", "requests")
    .run_function(download_model, gpu=GPU_CONFIG)
)

@app.function(
    gpu=GPU_CONFIG,
    image=embeddings_image,
    max_containers=4,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    import numpy as np
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from sentence_transformers import SentenceTransformer
    from typing import List, Optional, Union
    import base64
    import io
    from PIL import Image
    import requests

    web_app = FastAPI()

    # Load the model once when the container starts
    model = SentenceTransformer(MODEL_ID)
    
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

    class ModelInfoResponse(BaseModel):
        model_id: str
        vector_dimensions: int
        max_sequence_length: Optional[int] = None

    class EmbedImageRequest(BaseModel):
        images: List[str]  # List of base64 encoded images or URLs
        image_type: str = "base64"  # "base64" or "url"

    class EmbedImageResponse(BaseModel):
        embeddings: List[List[float]]

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

    def process_image(image_data: str, image_type: str) -> Image.Image:
        """Process image from base64 or URL"""
        if image_type == "base64":
            # Remove data URL prefix if present
            if image_data.startswith("data:image"):
                image_data = image_data.split(",")[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        elif image_type == "url":
            # Download image from URL
            response = requests.get(image_data, timeout=10)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
        else:
            raise ValueError(f"Unsupported image_type: {image_type}")
        
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        return image

    @web_app.get("/health")
    async def health_check():
        """
        Health check endpoint
        
        No request body required.
        
        Returns:
            - status: "ok" | "error"
            - model: str (model ID)
            - dimensions: int (vector dimensions)
        """
        try:
            # Test model with a simple embedding
            test_embedding = model.encode(["test"])
            return {"status": "ok", "model": MODEL_ID, "dimensions": len(test_embedding[0])}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @web_app.get("/info", response_model=ModelInfoResponse)
    async def get_model_info():
        """
        Get model information including vector dimensions
        
        No request body required.
        
        Returns:
            - model_id: str
            - vector_dimensions: int
            - max_sequence_length: int | null
        """
        try:
            # Get dimensions by encoding a test sentence
            test_embedding = model.encode(["test"])
            vector_dimensions = len(test_embedding[0])
            
            # Get max sequence length from model config if available
            max_length = getattr(model.tokenizer, 'model_max_length', None)
            if max_length and max_length > 100000:  # Some models return very large numbers
                max_length = 512  # Reasonable default
            
            return ModelInfoResponse(
                model_id=MODEL_ID,
                vector_dimensions=vector_dimensions,
                max_sequence_length=max_length
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

    @web_app.post("/embed", response_model=EmbedResponse)
    async def embed_texts(request: EmbedRequest):
        """
        Generate embeddings for the provided texts
        
        Request body:
        {
            "texts": ["string1", "string2", ...]  // Array of strings to embed
        }
        
        Returns:
        {
            "embeddings": [[float, float, ...], [float, float, ...], ...]  // Array of embedding vectors
        }
        """
        try:
            # Generate embeddings using SentenceTransformers
            embeddings = model.encode(request.texts)
            
            # Convert numpy arrays to lists
            embeddings_list = [embedding.tolist() for embedding in embeddings]

            return EmbedResponse(embeddings=embeddings_list)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

    @web_app.post("/similarity", response_model=SimilarityResponse)
    async def calculate_similarity(request: SimilarityRequest):
        """
        Calculate cosine similarity between two texts or vectors
        
        Request body (Option 1 - Compare two texts):
        {
            "text1": "first text to compare",
            "text2": "second text to compare"
        }
        
        Request body (Option 2 - Compare two vectors):
        {
            "vector1": [float, float, ...],  // First embedding vector
            "vector2": [float, float, ...]   // Second embedding vector (same dimension)
        }
        
        Returns:
        {
            "similarity": float  // Cosine similarity score between -1 and 1
        }
        """
        try:
            # Case 1: Both texts provided
            if request.text1 is not None and request.text2 is not None:
                # Get embeddings for both texts
                embeddings = model.encode([request.text1, request.text2])
                vector1, vector2 = embeddings[0].tolist(), embeddings[1].tolist()

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

    @web_app.post("/embedImage", response_model=EmbedImageResponse)
    async def embed_images(request: EmbedImageRequest):
        """
        Generate embeddings for the provided images
        
        Request body (Option 1 - Base64 encoded images):
        {
            "images": ["data:image/jpeg;base64,/9j/4AAQ...", "base64string2", ...],
            "image_type": "base64"
        }
        
        Request body (Option 2 - Image URLs):
        {
            "images": ["https://example.com/image1.jpg", "https://example.com/image2.png", ...],
            "image_type": "url"
        }
        
        Returns:
        {
            "embeddings": [[float, float, ...], [float, float, ...], ...]  // Array of image embedding vectors
        }
        """
        try:
            # Process images
            processed_images = []
            for image_data in request.images:
                image = process_image(image_data, request.image_type)
                processed_images.append(image)
            
            # Generate embeddings using SentenceTransformers CLIP model
            embeddings = model.encode(processed_images)
            
            # Convert numpy arrays to lists
            embeddings_list = [embedding.tolist() for embedding in embeddings]

            return EmbedImageResponse(embeddings=embeddings_list)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate image embeddings: {str(e)}")

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
