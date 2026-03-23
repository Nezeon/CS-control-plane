"""
SLA Awareness trait — Adds SLA constraint context and urgency framing.

Used by: triage_agent, escalation_agent
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry


@TraitRegistry.register
class SlaAwareness(BaseTrait):
    name = "sla_awareness"
    description = "Adds SLA countdown context and prioritizes actions to prevent breaches"

    def on_perceive(self, context: dict) -> str:
        # Check for SLA data in working memory or event payload
        event = context.get("event", {})
        payload = event.get("payload", {})
        sla_hours = payload.get("sla_hours_remaining")

        if sla_hours is not None:
            try:
                hours = float(sla_hours)
                if hours < 2:
                    return f"SLA CRITICAL: Only {hours:.1f} hours remaining until SLA breach. Treat as highest priority."
                elif hours < 8:
                    return f"SLA WARNING: {hours:.1f} hours until SLA breach. Prioritize this task."
                else:
                    return f"SLA STATUS: {hours:.1f} hours remaining. Monitor but not yet urgent."
            except (ValueError, TypeError):
                pass

        return (
            "SLA AWARENESS: Check for SLA constraints on this task. "
            "If ticket data is present, note time remaining until breach. "
            "Flag if SLA breach is imminent (< 2 hours)."
        )

    def on_think(self, task: str, context: dict) -> str:
        return (
            "Prioritize actions that prevent SLA violations. "
            "If an SLA breach is imminent, recommend immediate escalation or interim response. "
            "Consider whether the current approach will resolve within the SLA window."
        )
