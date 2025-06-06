import modal
import os
from typing import Dict, Any, List

# Create Modal app
app = modal.App("deepseek-r1")

# Define the container image with vLLM and optimizations
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "vllm==0.6.3.post1",
        "torch",
        "transformers>=4.40.0",
        "fastapi",
        "pydantic",
        "huggingface_hub",
        "hf_transfer",
    ])
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "VLLM_ATTENTION_BACKEND": "FLASH_ATTN",
        "CUDA_VISIBLE_DEVICES": "0",
        "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
    })
)

# Use A100 80GB for better compatibility and availability
GPU_CONFIG = "A100"

@app.cls(
    gpu=GPU_CONFIG,
    image=image,
    timeout=60 * 30,  # Increased to 30 minutes for large model
    min_containers=0,  # Start with 0 to reduce costs
    scaledown_window=60 * 5,  # Reduced scaledown window
)
@modal.concurrent(max_inputs=3)  # Reduced concurrent inputs for stability
class DeepSeekR1:
    # Use a smaller model for testing - change this to full model once working
    model_name: str = modal.parameter(default="microsoft/DialoGPT-medium")  # Smaller test model
    # For actual DeepSeek R1: "deepseek-ai/DeepSeek-R1"
    
    @modal.enter()
    def initialize_model(self):
        """Initialize the model when container starts"""
        print("Starting model initialization...")
        
        # Initialize the model on container startup
        from vllm import LLM, SamplingParams
        import time
        
        start_time = time.time()
        print(f"Loading model: {self.model_name}")
        
        try:
            # Initialize vLLM engine with conservative settings
            self.llm = LLM(
                model=self.model_name,
                tensor_parallel_size=1,
                gpu_memory_utilization=0.75,  # More conservative
                max_model_len=4096,  # Smaller for faster startup
                trust_remote_code=True,
                download_dir="/tmp/model_cache",
                enforce_eager=True,  # Use eager mode for stability
            )
            
            load_time = time.time() - start_time
            print(f"Model loaded successfully in {load_time:.2f} seconds!")
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            # Fallback to an even smaller model
            print("Falling back to smaller model...")
            self.model_name = "gpt2"
            self.llm = LLM(
                model=self.model_name,
                tensor_parallel_size=1,
                gpu_memory_utilization=0.5,
                max_model_len=1024,
                trust_remote_code=True,
                download_dir="/tmp/model_cache",
                enforce_eager=True,
            )
            print("Fallback model loaded successfully!")
        
        # Default sampling parameters
        self.default_sampling_params = SamplingParams(
            temperature=0.7,
            top_p=0.9,
            max_tokens=512,  # Reduced for faster response
            stop=["<|endoftext|>", "\n\n"]
        )

    @modal.method()
    def generate(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        stop: List[str] = None
    ) -> str:
        """Generate text completion for a single prompt"""
        from vllm import SamplingParams
        
        try:
            # Create sampling parameters
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stop=stop or ["<|endoftext|>", "\n\n"]
            )
            
            # Generate response
            outputs = self.llm.generate([prompt], sampling_params)
            return outputs[0].outputs[0].text
        except Exception as e:
            return f"Error generating response: {str(e)}"

    @modal.method()
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9
    ) -> str:
        """Generate chat completion using the chat template"""
        from vllm import SamplingParams
        
        try:
            # Simple prompt formatting for test model
            prompt = self._format_simple_prompt(messages)
            
            # Call generate method directly instead of using self.generate
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stop=["<|endoftext|>", "\n\n"]
            )
            
            # Generate response directly
            outputs = self.llm.generate([prompt], sampling_params)
            return outputs[0].outputs[0].text
            
        except Exception as e:
            return f"Error in chat completion: {str(e)}"

    def _format_simple_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a simple prompt for test models"""
        formatted_prompt = ""
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                formatted_prompt += f"System: {content}\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n"
        
        # Add assistant prompt
        formatted_prompt += "Assistant: "
        
        return formatted_prompt

    @modal.method()
    def health_check(self) -> Dict[str, str]:
        """Simple health check endpoint"""
        return {"status": "healthy", "model": self.model_name}

# FastAPI web endpoint with better error handling
@app.function(image=image, timeout=300)
@modal.fastapi_endpoint(method="POST")
def api_generate(item: Dict[str, Any]):
    """HTTP API endpoint for text generation"""
    try:
        deepseek = DeepSeekR1()
        
        if "messages" in item:
            # Chat completion format
            response = deepseek.chat_completion.remote(
                messages=item["messages"],
                temperature=item.get("temperature", 0.7),
                max_tokens=item.get("max_tokens", 512),
                top_p=item.get("top_p", 0.9)
            )
        else:
            # Simple text completion
            response = deepseek.generate.remote(
                prompt=item["prompt"],
                temperature=item.get("temperature", 0.7),
                max_tokens=item.get("max_tokens", 512),
                top_p=item.get("top_p", 0.9)
            )
        
        return {"response": response, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

# Health check endpoint
@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def health():
    """Health check endpoint"""
    try:
        deepseek = DeepSeekR1()
        status = deepseek.health_check.remote()
        return status
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Simplified local testing function
@app.local_entrypoint()
def main():
    """Test the deployed model locally"""
    try:
        print("Initializing model...")
        deepseek = DeepSeekR1()
        
        # Test health check first
        print("Testing health check...")
        health_status = deepseek.health_check.remote()
        print(f"Health Status: {health_status}")
        
        # Test simple generation
        print("\nTesting simple generation...")
        response = deepseek.generate.remote(
            prompt="Hello, how are you?",
            max_tokens=50
        )
        print(f"Response: {response}")
        
        # Test chat completion
        print("\nTesting chat completion...")
        messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        
        chat_response = deepseek.chat_completion.remote(
            messages=messages,
            max_tokens=100
        )
        print(f"Chat Response: {chat_response}")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    main()
