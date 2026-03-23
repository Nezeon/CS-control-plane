"""
Risk Assessment trait — Evaluates risk factors and adds risk scoring.

Used by: escalation_agent, health_monitor_agent,
         sow_agent (T3), deployment_intel_agent (T3)
"""

import json

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry

HIGH_RISK_KEYWORDS = [
    "critical", "outage", "breach", "failure", "down", "emergency",
    "data loss", "security", "production", "blocked",
]


@TraitRegistry.register
class RiskAssessment(BaseTrait):
    name = "risk_assessment"
    description = "Evaluates risk factors: health, tickets, complexity, contract value"

    def on_perceive(self, context: dict) -> str:
        return (
            "RISK ASSESSMENT: Assess risk factors for this task — "
            "customer health score, open ticket count, deployment complexity, "
            "contract value, and renewal proximity. "
            "Flag any factors that elevate risk."
        )

    def on_act_postprocess(self, result: dict, context: dict) -> dict:
        # Scan result for high-risk indicators
        text = json.dumps(result).lower()
        risk_signals = [kw for kw in HIGH_RISK_KEYWORDS if kw in text]

        if len(risk_signals) >= 3:
            risk_level = "critical"
        elif len(risk_signals) >= 2:
            risk_level = "high"
        elif len(risk_signals) >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        result["risk_level"] = risk_level
        if risk_signals:
            result["risk_signals"] = risk_signals

        return result

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Rate the overall risk level for this situation. "
            "Should this be escalated to a lead or the orchestrator? "
            "What specific mitigation actions are needed to reduce risk?"
        )
