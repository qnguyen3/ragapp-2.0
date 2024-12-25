import openai  # Changed to import the package directly
from typing import Optional

class FastMLXEndpoint:
    def __init__(self, api_key: str, url_base: str = "http://localhost:8000"):
        """
        Initialize both sync and async OpenAI clients with custom base URL.
        
        Args:
            api_key (str): The API key for authentication
            url_base (str): The base URL for the API endpoint. Defaults to "http://localhost:8000"
        """
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=url_base
        )
        self.async_client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=url_base
        )

    def generate(self, prompt: str, model_name: str = "mistral") -> str:
        """
        Generate text completion using the synchronous client.
        
        Args:
            prompt (str): The input prompt for generation
            model_name (str): The model to use for generation. Defaults to "mistral"
            
        Returns:
            str: The generated text completion
        """
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def agenerate(self, prompt: str, model_name: str = "mistral") -> str:
        """
        Generate text completion using the asynchronous client.
        
        Args:
            prompt (str): The input prompt for generation
            model_name (str): The model to use for generation. Defaults to "mistral"
            
        Returns:
            str: The generated text completion
        """
        response = await self.async_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
