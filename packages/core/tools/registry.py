"""
Tool System
===========
Registry and base classes for agent tools.
"""

from typing import List, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field
import inspect


class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class ToolDefinition(BaseModel):
    """Definition of a tool."""
    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    returns: str = "any"
    category: str = "general"
    tags: List[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool:
    """Base class for all tools."""

    name: str = "base_tool"
    description: str = "Base tool"
    category: str = "general"

    def __init__(self):
        self._definition = self._create_definition()

    def _create_definition(self) -> ToolDefinition:
        """Create tool definition from class attributes."""
        params = []
        
        # Get signature if callable
        if hasattr(self, 'execute') and callable(self.execute):
            sig = inspect.signature(self.execute)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    param_type = self._type_to_string(param.annotation)
                
                params.append(ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter {param_name}",
                    required=param.default == inspect.Parameter.empty,
                    default=None if param.default == inspect.Parameter.empty else param.default
                ))

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=params,
            category=self.category
        )

    def _type_to_string(self, type_hint) -> str:
        """Convert Python type to string representation."""
        type_map = {
            str: "string",
            int: "number",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null"
        }
        return type_map.get(type_hint, "string")

    @property
    def definition(self) -> ToolDefinition:
        """Get tool definition."""
        return self._definition

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters against definition."""
        for param_def in self._definition.parameters:
            if param_def.required and param_def.name not in params:
                return False
            
            if param_def.name in params and param_def.enum:
                if params[param_def.name] not in param_def.enum:
                    return False
        
        return True


class FunctionTool(BaseTool):
    """Tool wrapper for regular functions."""

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general"
    ):
        self.func = func
        self.name = name or func.__name__
        self.description = description or f"Tool: {self.name}"
        self.category = category
        super().__init__()

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the wrapped function."""
        try:
            if inspect.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)
            
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ToolRegistry:
    """Central registry for all available tools."""

    _instance = None
    _tools: Dict[str, BaseTool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def register_function(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general"
    ) -> None:
        """Register a function as a tool."""
        tool = FunctionTool(func, name, description, category)
        self.register(tool)

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def remove(self, name: str) -> bool:
        """Remove a tool by name."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return [tool.definition for tool in self._tools.values()]

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get tools by category."""
        return [
            tool for tool in self._tools.values()
            if tool.category == category
        ]

    def search_tools(self, query: str) -> List[BaseTool]:
        """Search tools by name or description."""
        query_lower = query.lower()
        return [
            tool for tool in self._tools.values()
            if query_lower in tool.name.lower() or
               query_lower in tool.description.lower()
        ]

    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {tool_name}")
        
        if not tool.validate_params(kwargs):
            return ToolResult(success=False, error="Invalid parameters")
        
        return await tool.execute(**kwargs)

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()


# Global registry instance
registry = ToolRegistry()


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general"
):
    """Decorator to register a function as a tool."""
    def decorator(func):
        tool_instance = FunctionTool(func, name, description, category)
        registry.register(tool_instance)
        return func
    return decorator
