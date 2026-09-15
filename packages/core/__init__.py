"""
Super Intelligent Agent - Core Package
======================================
"""

from .providers import (
    BaseProvider,
    ProviderConfig,
    ProviderType,
    ProviderRegistry,
    Message,
    ChatCompletion,
    create_provider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    OllamaProvider
)

from .agent import (
    Planner,
    Plan,
    PlanStep,
    Reasoner,
    ReasoningTrace,
    Executor,
    ExecutionResult,
    Reflector,
    Reflection,
    AgentLoop,
    AgentState,
    AgentLoopConfig
)

from .memory import (
    MemoryEntry,
    ShortTermMemory,
    LongTermMemory,
    ConversationMemory,
    MemoryManager
)

from .tools import (
    ToolParameter,
    ToolDefinition,
    ToolResult,
    BaseTool,
    FunctionTool,
    ToolRegistry,
    tool,
    registry
)

__version__ = "1.0.0"
__author__ = "Super Intelligent Agent Team"

__all__ = [
    # Providers
    "BaseProvider",
    "ProviderConfig",
    "ProviderType",
    "ProviderRegistry",
    "Message",
    "ChatCompletion",
    "create_provider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "OllamaProvider",
    
    # Agent
    "Planner",
    "Plan",
    "PlanStep",
    "Reasoner",
    "ReasoningTrace",
    "Executor",
    "ExecutionResult",
    "Reflector",
    "Reflection",
    "AgentLoop",
    "AgentState",
    "AgentLoopConfig",
    
    # Memory
    "MemoryEntry",
    "ShortTermMemory",
    "LongTermMemory",
    "ConversationMemory",
    "MemoryManager",
    
    # Tools
    "ToolParameter",
    "ToolDefinition",
    "ToolResult",
    "BaseTool",
    "FunctionTool",
    "ToolRegistry",
    "tool",
    "registry"
]
