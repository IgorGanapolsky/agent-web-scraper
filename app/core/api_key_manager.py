"""
API Key Manager for Claude Squad Persona-Specific Keys
Enables accountability and cost tracking per agent role
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.config.logging import get_logger

logger = get_logger(__name__)


class AgentRole(Enum):
    """Claude Squad agent roles"""

    CTO = "cto"
    CEO = "ceo"
    CMO = "cmo"
    CFO = "cfo"
    GENERAL = "general"


@dataclass
class APIKeyConfig:
    """API key configuration for an agent"""

    role: AgentRole
    anthropic_key: str
    langsmith_project: str
    cost_center: str


class APIKeyManager:
    """
    Manages persona-specific API keys for Claude Squad accountability
    """

    def __init__(self):
        self.api_configs = self._load_api_configs()
        self.current_role = AgentRole.GENERAL

    def _load_api_configs(self) -> dict[AgentRole, APIKeyConfig]:
        """Load API key configurations from environment"""
        configs = {}

        # CTO Configuration
        if os.getenv("ANTHROPIC_CTO_KEY"):
            configs[AgentRole.CTO] = APIKeyConfig(
                role=AgentRole.CTO,
                anthropic_key=os.getenv("ANTHROPIC_CTO_KEY"),
                langsmith_project="claude-squad-cto",
                cost_center="engineering",
            )

        # CEO Configuration
        if os.getenv("ANTHROPIC_CEO_KEY"):
            configs[AgentRole.CEO] = APIKeyConfig(
                role=AgentRole.CEO,
                anthropic_key=os.getenv("ANTHROPIC_CEO_KEY"),
                langsmith_project="claude-squad-ceo",
                cost_center="executive",
            )

        # CMO Configuration
        if os.getenv("ANTHROPIC_CMO_KEY"):
            configs[AgentRole.CMO] = APIKeyConfig(
                role=AgentRole.CMO,
                anthropic_key=os.getenv("ANTHROPIC_CMO_KEY"),
                langsmith_project="claude-squad-cmo",
                cost_center="marketing",
            )

        # CFO Configuration
        if os.getenv("ANTHROPIC_CFO_KEY"):
            configs[AgentRole.CFO] = APIKeyConfig(
                role=AgentRole.CFO,
                anthropic_key=os.getenv("ANTHROPIC_CFO_KEY"),
                langsmith_project="claude-squad-cfo",
                cost_center="finance",
            )

        # Fallback general configuration
        if os.getenv("ANTHROPIC_API_KEY"):
            configs[AgentRole.GENERAL] = APIKeyConfig(
                role=AgentRole.GENERAL,
                anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
                langsmith_project="claude-squad-general",
                cost_center="general",
            )

        return configs

    def set_current_role(self, role: AgentRole):
        """Set the current agent role for API calls"""
        if role not in self.api_configs:
            logger.warning(f"No API key configured for role {role}, using general key")
            role = AgentRole.GENERAL

        self.current_role = role
        logger.info(f"🔑 API key role set to: {role.value}")

    def get_current_config(self) -> Optional[APIKeyConfig]:
        """Get current API key configuration"""
        return self.api_configs.get(self.current_role)

    def get_anthropic_key(self, role: Optional[AgentRole] = None) -> str:
        """Get Anthropic API key for specific role"""
        target_role = role or self.current_role

        if target_role in self.api_configs:
            return self.api_configs[target_role].anthropic_key
        elif AgentRole.GENERAL in self.api_configs:
            logger.warning(f"No key for {target_role}, using general key")
            return self.api_configs[AgentRole.GENERAL].anthropic_key
        else:
            raise ValueError("No Anthropic API keys configured")

    def get_langsmith_project(self, role: Optional[AgentRole] = None) -> str:
        """Get LangSmith project name for role"""
        target_role = role or self.current_role

        if target_role in self.api_configs:
            return self.api_configs[target_role].langsmith_project
        else:
            return "claude-squad-general"

    def get_cost_center(self, role: Optional[AgentRole] = None) -> str:
        """Get cost center for role"""
        target_role = role or self.current_role

        if target_role in self.api_configs:
            return self.api_configs[target_role].cost_center
        else:
            return "general"

    def validate_setup(self) -> dict[str, bool]:
        """Validate API key setup"""
        validation = {}

        for role in AgentRole:
            validation[role.value] = role in self.api_configs

        validation["langsmith_configured"] = bool(os.getenv("LANGCHAIN_API_KEY"))
        validation["any_anthropic_key"] = len(self.api_configs) > 0

        return validation


# Global API key manager
_api_key_manager = None


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def set_agent_role(role: AgentRole):
    """Set current agent role globally"""
    manager = get_api_key_manager()
    manager.set_current_role(role)


def get_current_anthropic_key() -> str:
    """Get current Anthropic API key"""
    manager = get_api_key_manager()
    return manager.get_anthropic_key()


def get_current_langsmith_project() -> str:
    """Get current LangSmith project"""
    manager = get_api_key_manager()
    return manager.get_langsmith_project()
