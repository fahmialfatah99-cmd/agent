"""Root API router that includes all route modules"""
from fastapi import APIRouter
from .routes import chat, agents, providers, tools, memory

api_router = APIRouter()

# Include all route modules
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
