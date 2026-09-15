"""Agent management endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()

class AgentConfig(BaseModel):
    name: str
    provider: str = "openai"
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: Optional[str] = None
    enable_reflection: bool = True
    tools: Optional[List[str]] = None

class AgentInfo(BaseModel):
    id: str
    config: AgentConfig
    created_at: str
    status: str = "active"

# In-memory store (replace with database)
agents_store: Dict[str, AgentInfo] = {}

@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """List all available agents"""
    return list(agents_store.values())

@router.post("/", response_model=AgentInfo)
async def create_agent(config: AgentConfig):
    """Create a new agent with custom configuration"""
    import uuid
    from datetime import datetime
    
    agent_id = str(uuid.uuid4())
    agent_info = AgentInfo(
        id=agent_id,
        config=config,
        created_at=datetime.now().isoformat(),
        status="active"
    )
    agents_store[agent_id] = agent_info
    return agent_info

@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents_store[agent_id]

@router.put("/{agent_id}", response_model=AgentInfo)
async def update_agent(agent_id: str, config: AgentConfig):
    """Update agent configuration"""
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_info = agents_store[agent_id]
    agent_info.config = config
    return agent_info

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    del agents_store[agent_id]
    return {"status": "deleted", "agent_id": agent_id}
