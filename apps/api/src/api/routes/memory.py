"""Memory management endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()

class MemoryItem(BaseModel):
    id: str
    content: str
    type: str  # short_term, long_term, episodic
    created_at: str
    metadata: Optional[Dict[str, Any]] = None

class MemoryQueryRequest(BaseModel):
    query: str
    limit: int = 10
    memory_type: Optional[str] = None

# In-memory store (replace with actual database/vector store)
memory_store: List[MemoryItem] = []

@router.get("/", response_model=List[MemoryItem])
async def list_memories(memory_type: Optional[str] = None, limit: int = 50):
    """List stored memories"""
    memories = memory_store
    if memory_type:
        memories = [m for m in memories if m.type == memory_type]
    return memories[-limit:]

@router.post("/query", response_model=List[MemoryItem])
async def query_memory(request: MemoryQueryRequest):
    """Query memories (semantic search)"""
    # TODO: Implement actual vector search
    memories = memory_store
    if request.memory_type:
        memories = [m for m in memories if m.type == request.memory_type]
    return memories[-request.limit:]

@router.post("/add", response_model=MemoryItem)
async def add_memory(memory: MemoryItem):
    """Add a new memory"""
    # TODO: Implement actual memory storage with embedding
    memory_store.append(memory)
    return memory

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory by ID"""
    global memory_store
    initial_count = len(memory_store)
    memory_store = [m for m in memory_store if m.id != memory_id]
    
    if len(memory_store) == initial_count:
        raise HTTPException(status_code=404, detail=f"Memory not found: {memory_id}")
    
    return {"status": "deleted", "memory_id": memory_id}

@router.delete("/clear")
async def clear_memories(memory_type: Optional[str] = None):
    """Clear memories (optionally by type)"""
    global memory_store
    
    if memory_type:
        memory_store = [m for m in memory_store if m.type != memory_type]
        return {"status": "cleared", "type": memory_type}
    else:
        memory_store = []
        return {"status": "cleared", "type": "all"}
