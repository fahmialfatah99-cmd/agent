"""Chat endpoints"""
import os
import sys
import asyncio
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'packages'))

from core.providers import ProviderType, ProviderConfig, create_provider, Message
from core.agent import AgentLoop, AgentLoopConfig

# Register tools (Linux system + opencode-equivalent) ke global registry
import core.tools.linux_agent  # noqa: F401  (auto-register 7 tools)
import core.tools.opencode_tools  # noqa: F401  (auto-register 4 tools)
from core.tools import registry

from src.config.settings import settings

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    agent_id: str = "default"
    provider: Optional[str] = None
    model: Optional[str] = None
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2048


class ChatResponse(BaseModel):
    content: str
    agent_id: str
    model: str
    usage: Optional[dict] = None
    success: bool = True
    steps: Optional[List[Any]] = None
    tool_calls: Optional[List[Any]] = None


# Simple chat agent for direct completions (bypasses full agent loop for speed)
_chat_provider = None
_agents: Dict[str, AgentLoop] = {}


def _get_config(request: ChatMessage) -> ProviderConfig:
    """Build ProviderConfig from request and settings."""
    return ProviderConfig(
        provider_type=ProviderType.OPENAI,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL or "http://127.0.0.1:20128/v1",
        model=request.model or settings.DEFAULT_MODEL or "antigravity",
        temperature=request.temperature,
        max_tokens=request.max_tokens or 2048,
    )


async def _get_provider(request: ChatMessage):
    """Get or create a shared provider instance."""
    global _chat_provider
    if _chat_provider is None:
        config = _get_config(request)
        _chat_provider = create_provider(config.provider_type, config)
        await _chat_provider.initialize()
    return _chat_provider


@router.post("/completions", response_model=ChatResponse)
async def create_chat_completion(request: ChatMessage):
    """Send a message to the agent and get a response"""
    try:
        provider = await _get_provider(request)

        messages = [Message(role="user", content=request.message)]

        response = await provider.chat_completion(messages, temperature=request.temperature)

        content = ""
        if response.choices:
            content = response.choices[0].get("message", {}).get("content", "")

        return ChatResponse(
            content=content,
            agent_id=request.agent_id,
            model=response.model,
            usage=response.usage,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/agent/run")
async def run_agent_loop(
    goal: str,
    agent_id: str = "default",
    context: Optional[str] = None,
    enable_reflection: bool = True,
    max_iterations: int = 10,
):
    """Run the full agent loop (Planner → Reasoner → Executor → Reflector)."""
    try:
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL or "http://127.0.0.1:20128/v1",
            model=settings.DEFAULT_MODEL or "antigravity",
            temperature=0.7,
            max_tokens=2048,
        )
        provider = create_provider(config.provider_type, config)
        await provider.initialize()

        if agent_id not in _agents:
            agent_config = AgentLoopConfig(
                enable_reflection=enable_reflection,
                max_iterations=max_iterations,
            )
            _agents[agent_id] = AgentLoop(
                provider=provider,
                tool_registry=registry,
                config=agent_config,
            )

        agent = _agents[agent_id]
        result = await agent.run(goal=goal, context=context)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Agent failed"))

        steps = []
        for step in result.get("plan", {}).get("steps", []):
            if isinstance(step, dict):
                steps.append({
                    "id": step.get("id"),
                    "description": step.get("description"),
                    "status": step.get("status"),
                    "output": step.get("output"),
                })

        return ChatResponse(
            content=result.get("plan", {}).get("summary", "Agent task completed"),
            agent_id=agent_id,
            model=settings.DEFAULT_MODEL or "antigravity",
            steps=steps,
            success=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent loop error: {str(e)}")


@router.post("/stream")
async def stream_chat_completion(request: ChatMessage):
    """Stream a chat completion from the agent."""
    try:
        provider = await _get_provider(request)
        messages = [Message(role="user", content=request.message)]

        chunks = []
        async for chunk in provider.stream_chat_completion(messages, temperature=request.temperature):
            chunks.append(chunk)

        content = "".join(chunks)
        return {
            "content": content,
            "agent_id": request.agent_id,
            "model": request.model or settings.DEFAULT_MODEL or "antigravity",
            "streamed": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Retrieve conversation history for a session"""
    # TODO: Implement history retrieval
    return {"session_id": session_id, "messages": []}


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear conversation history for a session"""
    # TODO: Implement history deletion
    return {"status": "deleted", "session_id": session_id}