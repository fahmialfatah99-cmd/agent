"""
Memory System
=============
Provides short-term and long-term memory for the agent.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json
import os


class MemoryEntry(BaseModel):
    """A single memory entry."""
    id: str
    content: str
    type: str  # "episodic", "semantic", "procedural"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    importance: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embeddings: Optional[List[float]] = None  # Vector embedding


class ShortTermMemory(BaseModel):
    """Short-term working memory with limited capacity."""
    capacity: int = 10
    entries: List[MemoryEntry] = Field(default_factory=list)

    def add(self, entry: MemoryEntry) -> None:
        """Add an entry to short-term memory."""
        if len(self.entries) >= self.capacity:
            # Remove oldest entry
            self.entries.pop(0)
        self.entries.append(entry)

    def get_all(self) -> List[MemoryEntry]:
        """Get all entries."""
        return self.entries.copy()

    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()

    def search(self, query: str) -> List[MemoryEntry]:
        """Simple text search in short-term memory."""
        query_lower = query.lower()
        return [
            entry for entry in self.entries
            if query_lower in entry.content.lower()
        ]


class LongTermMemory:
    """
    Long-term memory with vector storage capabilities.
    Supports semantic search via embeddings.
    """

    def __init__(self, storage_backend: Optional[str] = None):
        """Initialize long-term memory."""
        self._entries: Dict[str, MemoryEntry] = {}
        self._index: Dict[str, List[str]] = {
            "episodic": [],
            "semantic": [],
            "procedural": []
        }
        self.storage_backend = storage_backend

    def add(self, entry: MemoryEntry) -> None:
        """Add an entry to long-term memory."""
        self._entries[entry.id] = entry
        if entry.type in self._index:
            self._index[entry.type].append(entry.id)

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get an entry by ID."""
        return self._entries.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        """Delete an entry by ID."""
        if entry_id in self._entries:
            entry = self._entries[entry_id]
            if entry.type in self._index:
                self._index[entry.type].remove(entry_id)
            del self._entries[entry_id]
            return True
        return False

    def search_by_type(self, memory_type: str) -> List[MemoryEntry]:
        """Search entries by type."""
        ids = self._index.get(memory_type, [])
        return [self._entries[id] for id in ids if id in self._entries]

    def search_by_importance(
        self,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Search entries by importance threshold."""
        filtered = [
            entry for entry in self._entries.values()
            if entry.importance >= min_importance
        ]
        sorted_entries = sorted(
            filtered,
            key=lambda x: (x.importance, x.access_count),
            reverse=True
        )
        return sorted_entries[:limit]

    def update_access(self, entry_id: str) -> None:
        """Update access count and timestamp for an entry."""
        if entry_id in self._entries:
            entry = self._entries[entry_id]
            entry.access_count += 1
            entry.updated_at = datetime.now()

    def get_all(self) -> List[MemoryEntry]:
        """Get all entries."""
        return list(self._entries.values())

    def size(self) -> int:
        """Get total number of entries."""
        return len(self._entries)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize long-term memory to a dictionary."""
        return {
            "entries": [
                {
                    **entry.model_dump(mode="json"),
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
                }
                for entry in self._entries.values()
            ]
        }

    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load long-term memory from a dictionary."""
        self._entries.clear()
        self._index = {"episodic": [], "semantic": [], "procedural": []}
        for item in data.get("entries", []):
            try:
                entry = MemoryEntry(
                    id=item["id"],
                    content=item.get("content", ""),
                    type=item.get("type", "episodic"),
                    created_at=datetime.fromisoformat(item["created_at"]) if item.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else None,
                    importance=item.get("importance", 0.5),
                    access_count=item.get("access_count", 0),
                    metadata=item.get("metadata", {}),
                    embeddings=item.get("embeddings"),
                )
                self._entries[entry.id] = entry
                if entry.type in self._index:
                    self._index[entry.type].append(entry.id)
            except (KeyError, ValueError):
                continue

    def save_to_file(self, path: str) -> None:
        """Persist long-term memory to a JSON file."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_from_file(self, path: str) -> None:
        """Load long-term memory from a JSON file."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.load_from_dict(data)
        except Exception:
            pass


class ConversationMemory(BaseModel):
    """Memory for conversation history."""
    max_turns: int = 20
    turns: List[Dict[str, str]] = Field(default_factory=list)

    def add_turn(self, role: str, content: str) -> None:
        """Add a conversation turn."""
        if len(self.turns) >= self.max_turns * 2:  # 2 messages per turn
            self.turns.pop(0)
            self.turns.pop(0)
        self.turns.append({"role": role, "content": content})

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.turns.copy()

    def get_summary_context(self) -> str:
        """Get a summary context from recent turns."""
        if not self.turns:
            return ""
        
        recent = self.turns[-6:]  # Last 3 turns
        return "\n".join([f"{t['role']}: {t['content']}" for t in recent])

    def clear(self) -> None:
        """Clear conversation history."""
        self.turns.clear()


class MemoryManager:
    """
    Central manager for all memory systems.
    Coordinates between short-term, long-term, and conversation memory.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize memory manager."""
        self.config = config or {}
        self.short_term = ShortTermMemory(
            capacity=self.config.get("stm_capacity", 10)
        )
        self.long_term = LongTermMemory(
            storage_backend=self.config.get("ltm_backend")
        )
        self.conversation = ConversationMemory(
            max_turns=self.config.get("max_turns", 20)
        )

    def add_to_short_term(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """Add entry to short-term memory."""
        import uuid
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )
        self.short_term.add(entry)
        return entry

    def consolidate_to_long_term(
        self,
        entry_id: Optional[str] = None,
        filter_fn=None
    ) -> List[MemoryEntry]:
        """Consolidate memories from short-term to long-term."""
        consolidated = []
        
        if entry_id:
            # Consolidate specific entry
            entries = self.short_term.search(entry_id)
        elif filter_fn:
            # Consolidate based on filter function
            entries = [e for e in self.short_term.get_all() if filter_fn(e)]
        else:
            # Consolidate high-importance entries
            entries = [
                e for e in self.short_term.get_all()
                if e.importance > 0.7
            ]

        for entry in entries:
            self.long_term.add(entry)
            consolidated.append(entry)

        return consolidated

    def add_conversation_turn(self, role: str, content: str) -> None:
        """Add a turn to conversation memory."""
        self.conversation.add_turn(role, content)
        
        # Also add to short-term memory
        self.add_to_short_term(
            content=f"{role}: {content}",
            memory_type="episodic",
            importance=0.6 if role == "user" else 0.5
        )

    def get_context(self, include_conversation: bool = True) -> str:
        """Get current memory context for the agent."""
        contexts = []

        if include_conversation:
            conv_context = self.conversation.get_summary_context()
            if conv_context:
                contexts.append(f"Recent conversation:\n{conv_context}")

        # Add important long-term memories
        important_memories = self.long_term.search_by_importance(
            min_importance=0.8,
            limit=5
        )
        if important_memories:
            mem_str = "\n".join([f"- {m.content}" for m in important_memories])
            contexts.append(f"Important memories:\n{mem_str}")

        return "\n\n".join(contexts)

    def search(
        self,
        query: str,
        scope: str = "all"  # "short", "long", "conversation", "all"
    ) -> List[MemoryEntry]:
        """Search across memory systems."""
        results = []

        if scope in ["short", "all"]:
            results.extend(self.short_term.search(query))

        if scope in ["long", "all"]:
            # Simple text search in long-term memory
            results.extend([
                entry for entry in self.long_term.get_all()
                if query.lower() in entry.content.lower()
            ])

        if scope in ["conversation", "all"]:
            # Search conversation history
            for turn in self.conversation.get_history():
                if query.lower() in turn["content"].lower():
                    results.append(MemoryEntry(
                        id=f"conv-{len(results)}",
                        content=turn["content"],
                        type="episodic"
                    ))

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "short_term_count": len(self.short_term.get_all()),
            "short_term_capacity": self.short_term.capacity,
            "long_term_count": self.long_term.size(),
            "conversation_turns": len(self.conversation.get_history()) // 2,
            "config": self.config
        }

    def clear_all(self) -> None:
        """Clear all memory systems."""
        self.short_term.clear()
        self.conversation.clear()
        # Note: We don't clear long-term memory by default
        # Use long_term.clear() if needed (would need to be implemented)

    def save_to_file(self, path: str) -> None:
        """Persist the whole memory manager (long-term) to a JSON file."""
        self.long_term.save_to_file(path)

    def load_from_file(self, path: str) -> None:
        """Load persisted memory from a JSON file."""
        self.long_term.load_from_file(path)

    def remember(self, content: str, importance: float = 0.6) -> MemoryEntry:
        """Explicitly store a fact into long-term memory (remember command)."""
        import uuid
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            type="semantic",
            importance=importance,
            metadata={},
        )
        self.long_term.add(entry)
        self.short_term.add(entry)
        return entry

    def recall(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Search returned relevant memories across systems (recall command)."""
        return self.search(query, scope="all")[:limit]
