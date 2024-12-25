import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from the backend package
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.llm import FastMLXEndpoint

# You can set your API key here or use environment variable
API_KEY = os.getenv("MLX_API_KEY", "test-key")
MODEL_NAME = "mlx-community/Llama-3.2-3B-Instruct-4bit"

def test_sync_generation():
    """Test synchronous generation with FastMLXEndpoint"""
    endpoint = FastMLXEndpoint(
        api_key=API_KEY,
        url_base="http://localhost:8000/v1"  # Adjust if your MLX server is running elsewhere
    )
    
    prompt = "Explain what makes Python a great programming language in 2-3 sentences."
    
    try:
        response = endpoint.generate(
            prompt=prompt,
            model_name=MODEL_NAME
        )
        print("\nSync Generation Test:")
        print(f"Prompt: {prompt}")
        print(f"Response: {response}\n")
        return True
    except Exception as e:
        print(f"Error in sync generation: {str(e)}")
        return False

async def test_async_generation():
    """Test asynchronous generation with FastMLXEndpoint"""
    endpoint = FastMLXEndpoint(
        api_key=API_KEY,
        url_base="http://localhost:8000/v1"  # Adjust if your MLX server is running elsewhere
    )
    
    prompt = "Write a short haiku about coding."
    
    try:
        response = await endpoint.agenerate(
            prompt=prompt,
            model_name=MODEL_NAME
        )
        print("\nAsync Generation Test:")
        print(f"Prompt: {prompt}")
        print(f"Response: {response}\n")
        return True
    except Exception as e:
        print(f"Error in async generation: {str(e)}")
        return False

def main():
    # Run synchronous test
    sync_success = test_sync_generation()
    
    # Run async test
    async_success = asyncio.run(test_async_generation())
    
    # Print overall results
    print("\nTest Results:")
    print(f"Synchronous Test: {'✓ Passed' if sync_success else '✗ Failed'}")
    print(f"Asynchronous Test: {'✓ Passed' if async_success else '✗ Failed'}")

if __name__ == "__main__":
    main()
