"""
Customer Sentiment trait — Tracks sentiment cues and mood shifts.

Used by: cso_orchestrator, value_lead, escalation_agent, health_monitor_agent,
         fathom_agent, and others across all tiers.
"""

import json

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry

NEGATIVE_CUES = [
    "frustrated", "angry", "disappointed", "unhappy", "confused",
    "escalate", "unacceptable", "cancel", "churn", "leaving",
]
POSITIVE_CUES = [
    "satisfied", "happy", "pleased", "great", "excellent",
    "thank", "impressed", "renewed", "expanded",
]


@TraitRegistry.register
class CustomerSentiment(BaseTrait):
    name = "customer_sentiment"
    description = "Tracks sentiment cues in context, flags mood shifts"

    def on_perceive(self, context: dict) -> str:
        return (
            "SENTIMENT AWARENESS: Watch for customer sentiment cues — "
            "frustration, satisfaction, urgency, confusion, or indifference. "
            "Note any mood shifts compared to previous interactions."
        )

    def on_act_postprocess(self, result: dict, context: dict) -> dict:
        # Scan result text for sentiment keywords
        text = json.dumps(result).lower()
        found_negative = [w for w in NEGATIVE_CUES if w in text]
        found_positive = [w for w in POSITIVE_CUES if w in text]

        if found_negative or found_positive:
            result["sentiment_cues"] = {
                "negative": found_negative,
                "positive": found_positive,
                "overall": "negative" if len(found_negative) > len(found_positive) else "positive",
            }

        return result

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Were there any sentiment signals you should flag? "
            "How does the customer likely feel about this situation? "
            "Should the tone of follow-up communications be adjusted?"
        )
