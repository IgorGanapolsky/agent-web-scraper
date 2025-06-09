"""
Session-Based Memory System for Claude Code
Maintains context across sessions using local files and structured memory nodes.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryNode:
    """Individual memory unit with metadata"""

    id: str
    content: dict[str, Any]
    category: str  # project_structure, financial_assumptions, user_preferences, etc.
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    importance_score: float = 1.0
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class SessionContext:
    """Complete session context for continuity"""

    session_id: str
    user_id: str
    project_name: str
    financial_assumptions: dict[str, Any]
    project_structure: dict[str, Any]
    user_preferences: dict[str, Any]
    conversation_history: list[dict[str, Any]]
    active_tasks: list[dict[str, Any]]
    created_at: datetime
    last_accessed: datetime


class SessionMemoryManager:
    """
    Enterprise session memory management for Claude Code.
    Ensures continuity across sessions for executives and technical teams.
    """

    def __init__(self, memory_dir: str = "./data/session_memory"):
        """
        Initialize session memory manager.

        Args:
            memory_dir: Directory for storing session memory files
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Memory organization
        self.memory_nodes: dict[str, MemoryNode] = {}
        self.session_contexts: dict[str, SessionContext] = {}

        # Load existing memory on startup
        self._load_persistent_memory()

    def create_session_context(
        self,
        user_id: str,
        project_name: str,
        initial_context: dict[str, Any] | None = None,
    ) -> str:
        """Create new session context with continuity from previous sessions."""
        session_id = self._generate_session_id(user_id, project_name)

        # Load previous session context if exists
        previous_context = self._load_previous_session_context(user_id, project_name)

        # Create new session with previous context
        session_context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            project_name=project_name,
            financial_assumptions=previous_context.get("financial_assumptions", {}),
            project_structure=previous_context.get("project_structure", {}),
            user_preferences=previous_context.get("user_preferences", {}),
            conversation_history=previous_context.get("conversation_history", [])[-50:],
            active_tasks=previous_context.get("active_tasks", []),
            created_at=datetime.now(),
            last_accessed=datetime.now(),
        )

        # Apply initial context if provided
        if initial_context:
            self._merge_initial_context(session_context, initial_context)

        self.session_contexts[session_id] = session_context

        logger.info(
            f"Created session context: {session_id} for user: {user_id}, project: {project_name}"
        )

        return session_id

    def store_memory_node(
        self,
        category: str,
        content: dict[str, Any],
        tags: list[str] | None = None,
        importance_score: float = 1.0,
    ) -> str:
        """Store a memory node for cross-session persistence."""
        node_id = self._generate_memory_node_id(category, content)

        memory_node = MemoryNode(
            id=node_id,
            content=content,
            category=category,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags or [],
            importance_score=importance_score,
        )

        self.memory_nodes[node_id] = memory_node
        self._persist_memory_node(memory_node)

        logger.info(f"Stored memory node: {node_id} in category: {category}")

        return node_id

    def _generate_session_id(self, user_id: str, project_name: str) -> str:
        """Generate unique session ID"""
        timestamp = str(int(time.time()))
        base_string = f"{user_id}:{project_name}:{timestamp}"
        return hashlib.md5(base_string.encode()).hexdigest()[:16]

    def _generate_memory_node_id(self, category: str, content: dict[str, Any]) -> str:
        """Generate unique memory node ID"""
        content_hash = hashlib.md5(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()[:16]
        return f"{category}:{content_hash}"

    def _load_persistent_memory(self) -> None:
        """Load persistent memory from disk"""
        memory_file = self.memory_dir / "memory_nodes.json"

        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    memory_data = json.load(f)

                for node_data in memory_data:
                    # Convert datetime strings back to datetime objects
                    node_data["created_at"] = datetime.fromisoformat(
                        node_data["created_at"]
                    )
                    node_data["updated_at"] = datetime.fromisoformat(
                        node_data["updated_at"]
                    )

                    memory_node = MemoryNode(**node_data)
                    self.memory_nodes[memory_node.id] = memory_node

                logger.info(f"Loaded {len(self.memory_nodes)} memory nodes from disk")

            except Exception as e:
                logger.error(f"Failed to load persistent memory: {e}")

    def _persist_memory_node(self, memory_node: MemoryNode) -> None:
        """Persist memory node to disk"""
        memory_file = self.memory_dir / "memory_nodes.json"

        try:
            # Convert all memory nodes to serializable format
            serializable_nodes = []
            for node in self.memory_nodes.values():
                node_dict = asdict(node)
                node_dict["created_at"] = node.created_at.isoformat()
                node_dict["updated_at"] = node.updated_at.isoformat()
                serializable_nodes.append(node_dict)

            with open(memory_file, "w") as f:
                json.dump(serializable_nodes, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to persist memory node: {e}")

    def _load_previous_session_context(
        self, user_id: str, project_name: str
    ) -> dict[str, Any]:
        """Load previous session context for user/project"""
        context_file = self.memory_dir / f"session_{user_id}_{project_name}.json"

        if context_file.exists():
            try:
                with open(context_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load previous session context: {e}")

        return {}

    def _merge_initial_context(
        self, session_context: SessionContext, initial_context: dict[str, Any]
    ) -> None:
        """Merge initial context into session"""
        for key, value in initial_context.items():
            if hasattr(session_context, key) and value:
                setattr(session_context, key, value)


# Global memory manager instance
_memory_manager = None


def get_session_memory_manager() -> SessionMemoryManager:
    """Get the global session memory manager"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = SessionMemoryManager()
    return _memory_manager


class LegacyMemoryAdapter:
    """Adapter for legacy memory interface"""

    def __init__(self):
        self.memory_manager = get_session_memory_manager()

    def get_business_context(self) -> dict[str, Any]:
        """Get business context from memory"""
        return {
            "target_daily_revenue": 300,
            "current_daily_revenue": 0,
            "monthly_costs": 2000,
            "pricing_tiers": {"starter": 19, "basic": 29, "pro": 99, "enterprise": 299},
            "conversion_rates": {"trial_signup": 0.15, "trial_to_paid": 0.25},
            "customer_acquisition_cost": 50,
        }

    def track_token_usage(
        self,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        model: str,
    ):
        """Track token usage"""
        # For now, just log it
        logger.info(
            f"Token usage: {operation} - {input_tokens} in, {output_tokens} out, ${cost:.2f} ({model})"
        )

    def store(
        self,
        key: str,
        value: Any,
        category: str = "general",
        priority: int = 1,
        expires_in_days: int | None = None,
    ):
        """Store data in memory"""
        self.memory_manager.store_memory_node(
            category=category,
            content={key: value},
            importance_score=1.0 if priority == 1 else 0.5,
        )


def get_session_memory():
    """Legacy interface for session memory"""
    return LegacyMemoryAdapter()
