"""
Root Cause Analysis trait — Systematic decomposition of symptoms vs. causes.

Used by: troubleshooter_agent (T3)
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry


@TraitRegistry.register
class RootCauseAnalysis(BaseTrait):
    name = "root_cause_analysis"
    description = "Guides systematic root cause analysis using 5 Whys methodology"

    def on_perceive(self, context: dict) -> str:
        return (
            "ROOT CAUSE LENS: Apply systematic root cause analysis. "
            "Distinguish between symptoms (what the customer sees) and causes "
            "(what actually went wrong). Consider the 5 Whys methodology — "
            "ask 'Why?' at least 3 times to dig past surface symptoms."
        )

    def on_think(self, task: str, context: dict) -> str:
        return (
            "What is the root cause vs. the symptom? "
            "What evidence supports your conclusion? "
            "Are there alternative explanations you haven't ruled out? "
            "Could this be caused by a recent change (deployment, config, infrastructure)?"
        )

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Did you identify a genuine root cause, or just a symptom? "
            "Is your evidence strong enough to be confident? "
            "Should this root cause be documented for pattern matching?"
        )
