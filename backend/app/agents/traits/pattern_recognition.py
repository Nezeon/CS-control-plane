"""
Pattern Recognition trait — Cross-customer and cross-issue pattern matching.

Used by: triage_agent (T3), troubleshooter_agent (T3), fathom_agent (T3),
         deployment_intel_agent (T3)
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry


@TraitRegistry.register
class PatternRecognition(BaseTrait):
    name = "pattern_recognition"
    description = "Searches for similar past issues across customers and recurring themes"

    def on_perceive(self, context: dict) -> str:
        return (
            "PATTERN SEARCH: Search for similar past issues across customers. "
            "Look for recurring themes in symptoms, root causes, or resolutions. "
            "Check if this matches any known failure modes or common scenarios."
        )

    def on_think(self, task: str, context: dict) -> str:
        return (
            "Have you seen this pattern before? What was the resolution last time? "
            "Can past solutions be adapted to this case? "
            "Are there cross-customer patterns that suggest a systemic issue?"
        )

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Did you leverage patterns from past cases effectively? "
            "Should this pattern be documented as a known issue for future reference?"
        )
