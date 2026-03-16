"""
Strategic Oversight trait — Adds big-picture strategic framing.

Used by: cso_orchestrator (T1), qbr_agent (T3)
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry


@TraitRegistry.register
class StrategicOversight(BaseTrait):
    name = "strategic_oversight"
    description = "Adds strategic context: cross-lane impact, portfolio health, organizational priorities"

    def on_perceive(self, context: dict) -> str:
        return (
            "STRATEGIC LENS: Consider the broader implications of this event. "
            "How does it affect the customer portfolio? Are there cross-lane impacts "
            "(support, value, delivery)? What resource allocation decisions might be needed?"
        )

    def on_think(self, task: str, context: dict) -> str:
        return (
            "Frame your analysis at the strategic level. "
            "What patterns span multiple customers or lanes? "
            "What organizational actions (not just tactical fixes) are needed? "
            "Consider long-term customer relationship impact."
        )

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Evaluate your strategic dimension: Did you consider cross-lane implications? "
            "Did you assess portfolio-level risk? Were your recommendations actionable "
            "at an organizational level, not just for the immediate issue?"
        )
