"""
Agent Factory — Registry and creation of agent instances from YAML profile IDs.

Each agent module registers its class at import time via AgentFactory.register().
The orchestrator and lane leads use AgentFactory.create() to instantiate agents on demand.

Usage:
    from app.agents.agent_factory import AgentFactory

    # In agent module:
    AgentFactory.register("triage_agent", TriageAgent)

    # In orchestrator/lead:
    agent = AgentFactory.create("triage_agent")
"""

import logging

logger = logging.getLogger("agent_factory")


class AgentFactory:
    """Creates agent instances by YAML profile ID."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, agent_id: str, agent_class: type) -> None:
        """Register an agent class for a YAML profile ID."""
        cls._registry[agent_id] = agent_class
        logger.debug(f"Registered agent: {agent_id} -> {agent_class.__name__}")

    @classmethod
    def create(cls, agent_id: str):
        """Create an agent instance by YAML profile ID."""
        agent_class = cls._registry.get(agent_id)
        if not agent_class:
            raise ValueError(
                f"No agent class registered for '{agent_id}'. "
                f"Available: {list(cls._registry.keys())}"
            )
        return agent_class()

    @classmethod
    def create_all(cls) -> dict:
        """Create instances of all registered agents."""
        return {aid: cls.create(aid) for aid in cls._registry}

    @classmethod
    def available(cls) -> list[str]:
        """List all registered agent IDs."""
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, agent_id: str) -> bool:
        """Check if an agent ID is registered."""
        return agent_id in cls._registry

    @classmethod
    def reset(cls) -> None:
        """Clear the registry (for testing)."""
        cls._registry.clear()
