"""
OpenAI Provider Implementation
==============================
Implementation of the OpenAI API provider.
"""

import asyncio
import time
from typing import List, Dict, Any, AsyncIterator, Optional
import httpx

from .base import BaseProvider, ProviderConfig, Message, ChatCompletion, ProviderType


class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = config.base_url or "https://api.openai.com/v1"

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self._initialized:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            if self.config.base_url:
                headers["api-key"] = self.config.api_key  # For Azure OpenAI
            
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.config.timeout)
            )
            self._initialized = True
            self.validate_config()

    async def chat_completion(
        self,
        messages: List[Message],
        **kwargs
    ) -> ChatCompletion:
        """Generate a chat completion using OpenAI API."""
        if not self._initialized:
            await self.initialize()

        payload = {
            "model": self.config.model,
            "messages": [msg.dict() for msg in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            **self.config.extra_params,
            **kwargs
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        for attempt in range(self.config.retry_attempts):
            try:
                response = await self.client.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()
                
                return ChatCompletion(
                    id=data["id"],
                    created=data["created"],
                    model=data["model"],
                    choices=data["choices"],
                    usage=data.get("usage", {})
                )
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def stream_chat_completion(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat completion from OpenAI API."""
        if not self._initialized:
            await self.initialize()

        payload = {
            "model": self.config.model,
            "messages": [msg.dict() for msg in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
            **self.config.extra_params,
            **kwargs
        }

        payload = {k: v for k, v in payload.items() if v is not None}

        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        if chunk["choices"][0].get("delta", {}).get("content"):
                            yield chunk["choices"][0]["delta"]["content"]
                    except json.JSONDecodeError:
                        continue

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self._initialized:
            await self.initialize()

        try:
            response = await self.client.get(f"/models/{self.config.model}")
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data["id"],
                    "object": data.get("object", "model"),
                    "created": data.get("created", 0),
                    "owned_by": data.get("owned_by", "openai")
                }
        except Exception:
            pass
        
        # Fallback if model info endpoint fails
        return {
            "id": self.config.model,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "openai"
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
        self._initialized = False
