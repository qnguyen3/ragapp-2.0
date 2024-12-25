from openai import OpenAI, AsyncOpenAI
from typing import Optional

class OpenAIEndpoint:
    def __init__(self, api_key: str):
        """Initialize both sync and async OpenAI clients."""
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)

    def generate(self, prompt: str, model_name: str = "gpt-3.5-turbo") -> str:
        """
        Generate text completion using the synchronous OpenAI client.
        
        Args:
            prompt (str): The input prompt for generation
            model_name (str): The model to use for generation. Defaults to "gpt-3.5-turbo"
            
        Returns:
            str: The generated text completion
        """
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def agenerate(self, prompt: str, model_name: str = "gpt-3.5-turbo") -> str:
        """
        Generate text completion using the asynchronous OpenAI client.
        
        Args:
            prompt (str): The input prompt for generation
            model_name (str): The model to use for generation. Defaults to "gpt-3.5-turbo"
            
        Returns:
            str: The generated text completion
        """
        response = await self.async_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
