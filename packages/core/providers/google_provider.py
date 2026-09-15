"""
Google Provider Implementation
==============================
Implementation of the Google Gemini API provider.
"""

import asyncio
from typing import List, Dict, Any, AsyncIterator, Optional
import httpx

from .base import BaseProvider, ProviderConfig, Message, ChatCompletion, ProviderType


class GoogleProvider(BaseProvider):
    """Google Gemini API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = config.base_url or "https://generativelanguage.googleapis.com/v1beta"

    async def initialize(self) -> None:
        """Initialize the Google client."""
        if not self._initialized:
            headers = {
                "Content-Type": "application/json"
            }
            
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.config.timeout),
                params={"key": self.config.api_key}
            )
            self._initialized = True
            self.validate_config()

    async def chat_completion(
        self,
        messages: List[Message],
        **kwargs
    ) -> ChatCompletion:
        """Generate a chat completion using Google Gemini API."""
        if not self._initialized:
            await self.initialize()

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            if msg.role != "system":  # System messages handled separately in Gemini
                contents.append({
                    "role": "model" if msg.role == "assistant" else "user",
                    "parts": [{"text": msg.content}]
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
                **self.config.extra_params,
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            }
        }

        # Remove None values
        payload["generationConfig"] = {
            k: v for k, v in payload["generationConfig"].items() 
            if v is not None
        }

        for attempt in range(self.config.retry_attempts):
            try:
                response = await self.client.post(
                    f"/models/{self.config.model}:generateContent",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                text_content = ""
                if "candidates" in data and len(data["candidates"]) > 0:
                    content = data["candidates"][0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        text_content = parts[0].get("text", "")

                return ChatCompletion(
                    id=f"gemini-{asyncio.get_event_loop().time()}",
                    created=int(asyncio.get_event_loop().time()),
                    model=self.config.model,
                    choices=[{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": text_content
                        },
                        "finish_reason": data.get("candidates", [{}])[0].get("finishReason", "stop")
                    }],
                    usage={}  # Google doesn't always provide token counts
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
        """Stream chat completion from Google Gemini API."""
        if not self._initialized:
            await self.initialize()

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            if msg.role != "system":
                contents.append({
                    "role": "model" if msg.role == "assistant" else "user",
                    "parts": [{"text": msg.content}]
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
                **self.config.extra_params
            }
        }

        # Note: Streaming implementation would need adjustment based on actual Gemini API
        # This is a simplified version
        result = await self.chat_completion(messages, **kwargs)
        yield result.choices[0]["message"]["content"]

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self._initialized:
            await self.initialize()

        try:
            response = await self.client.get(f"/models/{self.config.model}")
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data.get("name", self.config.model),
                    "object": "model",
                    "created": 0,
                    "owned_by": "google"
                }
        except Exception:
            pass
        
        return {
            "id": self.config.model,
            "object": "model",
            "created": 0,
            "owned_by": "google"
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
        self._initialized = False
