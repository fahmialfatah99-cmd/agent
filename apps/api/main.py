"""
FastAPI Backend for Super Intelligent Agent
============================================
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import os
import sys

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from core.providers import (
    ProviderType, 
    ProviderConfig, 
    create_provider,
    Message
)
from core.agent import AgentLoop, AgentLoopConfig
from core.memory import MemoryManager
from core.tools import registry

# Create FastAPI app
app = FastAPI(
    title="Super Intelligent Agent API",
    description="Advanced AI Agent with Planning, Reasoning, and Reflection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
agents: Dict[str, AgentLoop] = {}
memory_managers: Dict[str, MemoryManager] = {}


class ProviderRequest(BaseModel):
    """Request to configure a provider."""
    provider_type: str
    api_key: Optional[str] = None
    model: str = "gpt-4"
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


class AgentRequest(BaseModel):
    """Request to create/run an agent."""
    goal: str
    context: Optional[str] = None
    max_iterations: int = 10
    enable_reflection: bool = True
    enable_self_correction: bool = True
    verbose: bool = False


class ToolRegisterRequest(BaseModel):
    """Request to register a tool."""
    name: str
    description: str
    category: str = "general"


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Super Intelligent Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/providers/configure")
async def configure_provider(request: ProviderRequest):
    """Configure an LLM provider."""
    try:
        provider_type = ProviderType(request.provider_type)
        config = ProviderConfig(
            provider_type=provider_type,
            api_key=request.api_key or os.getenv("LLM_API_KEY"),
            model=request.model,
            base_url=request.base_url,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        provider = create_provider(provider_type, config)
        await provider.initialize()
        
        return {
            "success": True,
            "message": f"Provider {request.provider_type} configured successfully",
            "model": request.model
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/agents/create")
async def create_agent(agent_id: str, provider_config: ProviderRequest):
    """Create a new agent instance."""
    try:
        provider_type = ProviderType(provider_config.provider_type)
        config = ProviderConfig(
            provider_type=provider_type,
            api_key=provider_config.api_key or os.getenv("LLM_API_KEY"),
            model=provider_config.model,
            temperature=provider_config.temperature,
            max_tokens=provider_config.max_tokens
        )
        
        provider = create_provider(provider_type, config)
        await provider.initialize()
        
        agent_config = AgentLoopConfig(
            max_iterations=provider_config.max_tokens // 1000,
            enable_reflection=True,
            enable_self_correction=True,
            verbose=False
        )
        
        agent = AgentLoop(provider=provider, config=agent_config)
        agents[agent_id] = agent
        
        memory_managers[agent_id] = MemoryManager()
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": "Agent created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, request: AgentRequest):
    """Run an agent to achieve a goal."""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        agent = agents[agent_id]
        result = await agent.run(
            goal=request.goal,
            context=request.context
        )
        
        return {
            "success": result.get("success", False),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get agent status."""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents[agent_id]
    return {
        "agent_id": agent_id,
        "state": agent.get_state()
    }


@app.post("/agents/{agent_id}/reset")
async def reset_agent(agent_id: str):
    """Reset an agent."""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agents[agent_id].reset()
    return {"success": True, "message": "Agent reset successfully"}


@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent."""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    del agents[agent_id]
    if agent_id in memory_managers:
        del memory_managers[agent_id]
    
    return {"success": True, "message": "Agent deleted successfully"}


@app.get("/tools/list")
async def list_tools():
    """List all registered tools."""
    tools = registry.list_tools()
    return {
        "tools": [tool.dict() for tool in tools],
        "count": len(tools)
    }


@app.post("/tools/register")
async def register_tool(request: ToolRegisterRequest):
    """Register a new tool."""
    # This is a placeholder - actual tool registration would need function code
    return {
        "success": True,
        "message": f"Tool {request.name} registered (placeholder)"
    }


@app.get("/memory/{agent_id}/stats")
async def get_memory_stats(agent_id: str):
    """Get memory statistics for an agent."""
    if agent_id not in memory_managers:
        raise HTTPException(status_code=404, detail="Memory manager not found")
    
    stats = memory_managers[agent_id].get_stats()
    return stats


@app.websocket("/ws/agents/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for streaming agent events."""
    if agent_id not in agents:
        await websocket.close(code=4004, reason="Agent not found")
        return
    
    await websocket.accept()
    agent = agents[agent_id]
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "run":
                async for event in agent.run_streaming(
                    goal=data.get("goal", ""),
                    context=data.get("context")
                ):
                    await websocket.send_json(event)
                    
    except Exception as e:
        await websocket.send_json({"event": "error", "error": str(e)})


# Sample built-in tools
@registry.register_function
async def search_web(query: str) -> str:
    """Search the web for information."""
    # Placeholder - implement actual web search
    return f"Search results for: {query}"


@registry.register_function
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        # Safe evaluation
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@registry.register_function
async def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
