"""Tool management endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()

class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    enabled: bool = True

class ToolRegisterRequest(BaseModel):
    name: str
    description: str
    code: str  # Python code for the tool function

# In-memory tool registry (replace with actual implementation)
tools_store: Dict[str, ToolInfo] = {
    "web_search": ToolInfo(
        name="web_search",
        description="Search the web for information",
        parameters={"query": {"type": "string", "required": True}},
        enabled=True
    ),
    "calculator": ToolInfo(
        name="calculator",
        description="Perform mathematical calculations",
        parameters={"expression": {"type": "string", "required": True}},
        enabled=True
    ),
    "get_time": ToolInfo(
        name="get_time",
        description="Get current time and date",
        parameters={},
        enabled=True
    )
}

@router.get("/", response_model=List[ToolInfo])
async def list_tools():
    """List all available tools"""
    return [tool for tool in tools_store.values() if tool.enabled]

@router.post("/register", response_model=ToolInfo)
async def register_tool(request: ToolRegisterRequest):
    """Register a custom tool"""
    # TODO: Implement actual tool registration with code validation
    tool_info = ToolInfo(
        name=request.name,
        description=request.description,
        parameters={"custom": True},
        enabled=True
    )
    tools_store[request.name] = tool_info
    return tool_info

@router.get("/{tool_name}", response_model=ToolInfo)
async def get_tool(tool_name: str):
    """Get tool by name"""
    if tool_name not in tools_store:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    return tools_store[tool_name]

@router.put("/{tool_name}/toggle")
async def toggle_tool(tool_name: str):
    """Enable or disable a tool"""
    if tool_name not in tools_store:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    tool = tools_store[tool_name]
    tool.enabled = not tool.enabled
    return {"name": tool_name, "enabled": tool.enabled}

@router.delete("/{tool_name}")
async def delete_tool(tool_name: str):
    """Delete a custom tool"""
    if tool_name not in tools_store:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    del tools_store[tool_name]
    return {"status": "deleted", "tool_name": tool_name}
