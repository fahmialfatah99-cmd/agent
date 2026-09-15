"""
Provider Abstraction Layer
==========================
Base classes and interfaces for LLM providers.
Supports multiple providers: OpenAI, Anthropic, Google, Local models, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncIterator
from pydantic import BaseModel, Field
from enum import Enum


class ProviderType(str, Enum):
    """Supported provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"


class Message(BaseModel):
    """Chat message structure."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ChatCompletion(BaseModel):
    """Chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]


class ProviderConfig(BaseModel):
    """Configuration for providers."""
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 30
    retry_attempts: int = 3
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider connection."""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Message],
        **kwargs
    ) -> ChatCompletion:
        """Generate a chat completion."""
        pass

    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat completion responses."""
        pass

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        pass

    async def close(self) -> None:
        """Close the provider connection."""
        self._initialized = False

    def validate_config(self) -> bool:
        """Validate the provider configuration."""
        if not self.config.model:
            raise ValueError("Model name is required")
        return True


class ProviderRegistry:
    """Registry for managing provider instances."""

    _providers: Dict[str, BaseProvider] = {}
    _configs: Dict[str, ProviderConfig] = {}

    @classmethod
    def register(cls, name: str, provider: BaseProvider, config: ProviderConfig) -> None:
        """Register a provider instance."""
        cls._providers[name] = provider
        cls._configs[name] = config

    @classmethod
    def get(cls, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return cls._providers.get(name)

    @classmethod
    def get_config(cls, name: str) -> Optional[ProviderConfig]:
        """Get provider config by name."""
        return cls._configs.get(name)

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers."""
        return list(cls._providers.keys())

    @classmethod
    def remove(cls, name: str) -> bool:
        """Remove a provider from the registry."""
        if name in cls._providers:
            del cls._providers[name]
            if name in cls._configs:
                del cls._configs[name]
            return True
        return False


def create_provider(provider_type: ProviderType, config: ProviderConfig) -> BaseProvider:
    """Factory function to create provider instances."""
    if provider_type == ProviderType.OPENAI:
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(config)
    elif provider_type == ProviderType.ANTHROPIC:
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(config)
    elif provider_type == ProviderType.GOOGLE:
        from .google_provider import GoogleProvider
        return GoogleProvider(config)
    elif provider_type == ProviderType.OLLAMA:
        from .ollama_provider import OllamaProvider
        return OllamaProvider(config)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
