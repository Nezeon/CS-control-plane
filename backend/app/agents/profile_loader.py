"""
YAML Configuration Loader for the Agent Hierarchy.

Loads org_structure.yaml, agent_profiles.yaml, pipeline.yaml, and workflows.yaml
at first access and caches them in memory. Singleton pattern — one instance per process.

Usage:
    from app.agents.profile_loader import ProfileLoader
    loader = ProfileLoader.get()
    profile = loader.get_agent_profile("triage_agent")
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger("profile_loader")

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


class ProfileLoader:
    _instance = None

    def __init__(self):
        self._profiles: dict | None = None
        self._org_structure: dict | None = None
        self._pipeline_config: dict | None = None
        self._workflows: dict | None = None

    @classmethod
    def get(cls) -> "ProfileLoader":
        """Get or create the singleton ProfileLoader instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_all()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None

    def _load_all(self) -> None:
        """Load all YAML config files from the config directory."""
        logger.info(f"Loading YAML configs from {CONFIG_DIR}")

        self._org_structure = yaml.safe_load(
            (CONFIG_DIR / "org_structure.yaml").read_text(encoding="utf-8")
        )
        raw_profiles = yaml.safe_load(
            (CONFIG_DIR / "agent_profiles.yaml").read_text(encoding="utf-8")
        )
        # Unwrap the top-level "agents" key if present
        self._profiles = raw_profiles.get("agents", raw_profiles) if isinstance(raw_profiles, dict) else raw_profiles
        self._pipeline_config = yaml.safe_load(
            (CONFIG_DIR / "pipeline.yaml").read_text(encoding="utf-8")
        )
        self._workflows = yaml.safe_load(
            (CONFIG_DIR / "workflows.yaml").read_text(encoding="utf-8")
        )

        agent_count = len(self._profiles) if self._profiles else 0
        logger.info(f"Loaded {agent_count} agent profiles")

    # ── Agent Profiles ──────────────────────────────────────────────

    def get_agent_profile(self, agent_id: str) -> dict | None:
        """Get a single agent profile by ID."""
        if self._profiles is None:
            return None
        return self._profiles.get(agent_id)

    def get_all_profiles(self) -> dict:
        """Get all agent profiles as {agent_id: profile_dict}."""
        return self._profiles or {}

    def get_agent_ids(self) -> list[str]:
        """Get all agent IDs."""
        return list(self._profiles.keys()) if self._profiles else []

    # ── Organization Structure ──────────────────────────────────────

    def get_org_structure(self) -> dict:
        """Get the full organization structure."""
        return self._org_structure or {}

    def get_agents_in_tier(self, tier: int) -> list[str]:
        """Get all agent IDs in a specific tier (1-4)."""
        org = self._org_structure or {}
        hierarchy = org.get("organization", {}).get("hierarchy", {})
        tier_key = f"tier_{tier}"
        tier_data = hierarchy.get(tier_key, {})
        return tier_data.get("agents", [])

    def get_lane_for_agent(self, agent_id: str) -> str | None:
        """Get the lane an agent belongs to (support/value/delivery/None)."""
        profile = self.get_agent_profile(agent_id)
        if profile is None:
            return None
        return profile.get("lane")

    def get_agents_in_lane(self, lane: str) -> list[str]:
        """Get all agent IDs in a lane (including the lead)."""
        org = self._org_structure or {}
        lanes = org.get("organization", {}).get("lanes", {})
        lane_data = lanes.get(lane, {})
        agents = []
        lead = lane_data.get("lead")
        if lead:
            agents.append(lead)
        agents.extend(lane_data.get("specialists", []))
        return agents

    def get_reports_to(self, agent_id: str) -> str | None:
        """Get the agent ID this agent reports to."""
        profile = self.get_agent_profile(agent_id)
        if profile is None:
            return None
        return profile.get("reports_to")

    def get_manages(self, agent_id: str) -> list[str]:
        """Get the agent IDs this agent manages."""
        profile = self.get_agent_profile(agent_id)
        if profile is None:
            return []
        return profile.get("manages", [])

    # ── Pipeline Configuration ──────────────────────────────────────

    def get_pipeline_config(self) -> dict:
        """Get the full pipeline configuration."""
        return self._pipeline_config or {}

    def get_pipeline_for_tier(self, tier: int) -> dict | None:
        """Get the pipeline config for a specific tier."""
        pipelines = (self._pipeline_config or {}).get("pipelines", {})
        tier_map = {
            1: "orchestrator",
            2: "specialist",
            3: "specialist",
            4: "foundation",
        }
        key = tier_map.get(tier)
        return pipelines.get(key) if key else None

    # ── Workflows ───────────────────────────────────────────────────

    def get_all_workflows(self) -> dict:
        """Get all workflow definitions."""
        return (self._workflows or {}).get("workflows", {})

    def get_workflow_for_event(self, event_type: str) -> dict | None:
        """Find the workflow triggered by a specific event type."""
        workflows = self.get_all_workflows()
        for workflow_name, workflow in workflows.items():
            if event_type in workflow.get("trigger_events", []):
                return {"name": workflow_name, **workflow}
        return None
