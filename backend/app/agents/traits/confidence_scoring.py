"""
Confidence Scoring trait — Tracks and scores confidence levels in agent outputs.

Used by: agents that need to express certainty levels.
"""

import json

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry

LOW_CONFIDENCE_CUES = [
    "unclear", "uncertain", "might", "possibly", "not sure",
    "limited data", "insufficient", "ambiguous", "unknown",
]
HIGH_CONFIDENCE_CUES = [
    "confirmed", "verified", "clearly", "definitely", "certain",
    "strong evidence", "consistent", "well-documented", "established",
]


@TraitRegistry.register
class ConfidenceScoring(BaseTrait):
    name = "confidence_scoring"
    description = "Tracks confidence levels in agent reasoning and outputs"

    def on_think(self, task: str, context: dict) -> str:
        return (
            "CONFIDENCE TRACKING: As you reason, assess your confidence level "
            "(high / medium / low) for each claim or recommendation. "
            "Flag areas where data is insufficient or conclusions are speculative. "
            "Prefer concrete evidence over assumptions."
        )

    def on_act_postprocess(self, result: dict, context: dict) -> dict:
        text = json.dumps(result).lower()
        low_found = [w for w in LOW_CONFIDENCE_CUES if w in text]
        high_found = [w for w in HIGH_CONFIDENCE_CUES if w in text]

        low_count = len(low_found)
        high_count = len(high_found)
        total = low_count + high_count

        if total > 0:
            score = round(high_count / total, 2)
        else:
            score = 0.7  # Default medium-high when no explicit cues

        result["confidence"] = {
            "score": score,
            "level": "high" if score >= 0.7 else ("medium" if score >= 0.4 else "low"),
            "low_cues": low_found,
            "high_cues": high_found,
        }
        return result

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Review your confidence level. Where were you most certain? "
            "Where did you have to make assumptions? "
            "What additional data would increase your confidence?"
        )
