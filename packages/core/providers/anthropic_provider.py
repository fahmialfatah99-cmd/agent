"""
Anthropic Provider Implementation
=================================
Implementation of the Anthropic Claude API provider.
"""

import asyncio
from typing import List, Dict, Any, AsyncIterator, Optional
import httpx

from .base import BaseProvider, ProviderConfig, Message, ChatCompletion, ProviderType


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = config.base_url or "https://api.anthropic.com/v1"

    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self._initialized:
            headers = {
                "x-api-key": self.config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
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
        """Generate a chat completion using Anthropic API."""
        if not self._initialized:
            await self.initialize()

        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": "assistant" if msg.role == "assistant" else "user",
                    "content": msg.content
                })

        payload = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            **self.config.extra_params,
            **kwargs
        }

        if system_message:
            payload["system"] = system_message

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        for attempt in range(self.config.retry_attempts):
            try:
                response = await self.client.post("/messages", json=payload)
                response.raise_for_status()
                data = response.json()
                
                return ChatCompletion(
                    id=data["id"],
                    created=int(asyncio.get_event_loop().time()),
                    model=data["model"],
                    choices=[{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": data["content"][0]["text"] if data["content"] else ""
                        },
                        "finish_reason": data.get("stop_reason", "stop")
                    }],
                    usage={
                        "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                        "total_tokens": (
                            data.get("usage", {}).get("input_tokens", 0) +
                            data.get("usage", {}).get("output_tokens", 0)
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
        """Stream chat completion from Anthropic API."""
        if not self._initialized:
            await self.initialize()

        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": "assistant" if msg.role == "assistant" else "user",
                    "content": msg.content
                })

        payload = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
            **self.config.extra_params,
            **kwargs
        }

        if system_message:
            payload["system"] = system_message

        payload = {k: v for k, v in payload.items() if v is not None}

        async with self.client.stream("POST", "/messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    try:
                        import json
                        chunk = json.loads(data)
                        if chunk.get("type") == "content_block_delta":
                            yield chunk.get("delta", {}).get("text", "")
                    except json.JSONDecodeError:
                        continue

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "id": self.config.model,
            "object": "model",
            "created": 0,
            "owned_by": "anthropic"
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
        self._initialized = False
