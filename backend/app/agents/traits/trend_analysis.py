"""
Trend Analysis trait — Frames analysis around patterns and trajectory.

Used by: value_lead (T2), health_monitor_agent (T3), qbr_agent (T3)
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry


@TraitRegistry.register
class TrendAnalysis(BaseTrait):
    name = "trend_analysis"
    description = "Focuses on trend detection: direction, velocity, and trajectory"

    def on_perceive(self, context: dict) -> str:
        return (
            "TREND LENS: Look for trends in the data. Is this event a one-off "
            "or part of a recurring pattern? Compare to recent data points. "
            "Consider historical context — has the customer been improving or declining?"
        )

    def on_think(self, task: str, context: dict) -> str:
        return (
            "Identify the trend direction (improving, declining, or stable), "
            "the velocity of change (rapid vs. gradual), and the likely trajectory "
            "if no intervention occurs. What leading indicators support your assessment?"
        )

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Did you identify the trend correctly? Were there data points you missed? "
            "How confident are you in the trajectory prediction?"
        )
