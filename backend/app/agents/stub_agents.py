"""Stub agents — placeholders for Phase 7 implementation."""

from app.agents.base_agent import BaseAgent


class TroubleshootAgent(BaseAgent):
    """Analyzes support bundles for root cause. (Stub — Phase 7)"""

    agent_name = "troubleshooter"
    agent_type = "support"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        return {
            "success": True,
            "output": {"message": "Troubleshooter agent not yet implemented (Phase 7)."},
            "reasoning_summary": "Stub agent — awaiting Phase 7 implementation.",
        }


class EscalationAgent(BaseAgent):
    """Generates escalation summary packages. (Stub — Phase 7)"""

    agent_name = "escalation_summary"
    agent_type = "support"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        return {
            "success": True,
            "output": {"message": "Escalation Summary agent not yet implemented (Phase 7)."},
            "reasoning_summary": "Stub agent — awaiting Phase 7 implementation.",
        }


class QBRAgent(BaseAgent):
    """Generates quarterly business review content. (Stub — Phase 7)"""

    agent_name = "qbr_value"
    agent_type = "value"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        return {
            "success": True,
            "output": {"message": "QBR Value agent not yet implemented (Phase 7)."},
            "reasoning_summary": "Stub agent — awaiting Phase 7 implementation.",
        }


class SOWAgent(BaseAgent):
    """Pre-deployment checklists and readiness. (Stub — Phase 7)"""

    agent_name = "sow_prerequisite"
    agent_type = "value"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        return {
            "success": True,
            "output": {"message": "SOW Prerequisite agent not yet implemented (Phase 7)."},
            "reasoning_summary": "Stub agent — awaiting Phase 7 implementation.",
        }


class DeploymentIntelAgent(BaseAgent):
    """Monitors deployment health and patterns. (Stub — Phase 7)"""

    agent_name = "deployment_intelligence"
    agent_type = "value"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        return {
            "success": True,
            "output": {"message": "Deployment Intelligence agent not yet implemented (Phase 7)."},
            "reasoning_summary": "Stub agent — awaiting Phase 7 implementation.",
        }
