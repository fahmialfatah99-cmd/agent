"""
Ollama Provider Implementation
==============================
Implementation of the Ollama local LLM provider.
"""

import asyncio
from typing import List, Dict, Any, AsyncIterator, Optional
import httpx

from .base import BaseProvider, ProviderConfig, Message, ChatCompletion, ProviderType


class OllamaProvider(BaseProvider):
    """Ollama local LLM provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = config.base_url or "http://localhost:11434"

    async def initialize(self) -> None:
        """Initialize the Ollama client."""
        if not self._initialized:
            headers = {
                "Content-Type": "application/json"
            }
            
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
        """Generate a chat completion using Ollama API."""
        if not self._initialized:
            await self.initialize()

        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        payload = {
            "model": self.config.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                **self.config.extra_params,
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            }
        }

        # Remove None values from options
        payload["options"] = {
            k: v for k, v in payload["options"].items() 
            if v is not None
        }

        for attempt in range(self.config.retry_attempts):
            try:
                response = await self.client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                
                return ChatCompletion(
                    id=f"ollama-{asyncio.get_event_loop().time()}",
                    created=int(asyncio.get_event_loop().time()),
                    model=self.config.model,
                    choices=[{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": data.get("message", {}).get("content", "")
                        },
                        "finish_reason": "stop" if data.get("done", False) else "length"
                    }],
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": (
                            data.get("prompt_eval_count", 0) +
                            data.get("eval_count", 0)
                        )
                    }
                )
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def stream_chat_completion(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat completion from Ollama API."""
        if not self._initialized:
            await self.initialize()

        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        payload = {
            "model": self.config.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                **self.config.extra_params
            }
        }

        payload["options"] = {
            k: v for k, v in payload["options"].items() 
            if v is not None
        }

        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                try:
                    import json
                    chunk = json.loads(line)
                    if chunk.get("message", {}).get("content"):
                        yield chunk["message"]["content"]
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self._initialized:
            await self.initialize()

        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                for model in models:
                    if model.get("name") == self.config.model:
                        return {
                            "id": model.get("name"),
                            "object": "model",
                            "created": model.get("modified_at", ""),
                            "owned_by": "ollama"
                        }
        except Exception:
            pass
        
        return {
            "id": self.config.model,
            "object": "model",
            "created": 0,
            "owned_by": "ollama"
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
        self._initialized = False
