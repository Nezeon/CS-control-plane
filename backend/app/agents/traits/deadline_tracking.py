"""
Deadline Tracking trait — Adds deadline urgency context and prioritization.

Used by: sow_agent, deployment_intel_agent
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry


@TraitRegistry.register
class DeadlineTracking(BaseTrait):
    name = "deadline_tracking"
    description = "Tracks QBR dates, SOW milestones, deployment windows, and renewal dates"

    def on_perceive(self, context: dict) -> str:
        return (
            "DEADLINE AWARENESS: Check for deadline constraints — "
            "QBR dates, SOW milestones, deployment windows, contract renewal dates. "
            "Flag anything due within 7 days as urgent, within 30 days as upcoming."
        )

    def on_think(self, task: str, context: dict) -> str:
        return (
            "Prioritize by deadline proximity. "
            "What must be completed before the next milestone? "
            "Are there dependencies that could cause delays? "
            "Recommend timeline adjustments if the current pace won't meet deadlines."
        )

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Did you account for all relevant deadlines? "
            "Are the recommended timelines realistic given current workload?"
        )
