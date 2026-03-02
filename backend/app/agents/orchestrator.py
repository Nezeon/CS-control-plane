import logging
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.agents.call_intel_agent import CallIntelAgent
from app.agents.deployment_intel_agent import DeploymentIntelAgent
from app.agents.escalation_agent import EscalationAgent
from app.agents.health_monitor import HealthMonitorAgent
from app.agents.memory_agent import CustomerMemoryAgent
from app.agents.qbr_agent import QBRAgent
from app.agents.sow_agent import SOWAgent
from app.agents.triage_agent import TicketTriageAgent
from app.agents.troubleshoot_agent import TroubleshootAgent

logger = logging.getLogger("agents.orchestrator")

# Event type → agent name routing table
EVENT_ROUTING = {
    "jira_ticket_created": "ticket_triage",
    "jira_ticket_updated": "ticket_triage",
    "ticket_escalated": "escalation_summary",
    "support_bundle_uploaded": "troubleshooter",
    "zoom_call_completed": "call_intelligence",
    "fathom_recording_ready": "call_intelligence",
    "daily_health_check": "health_monitor",
    "manual_health_check": "health_monitor",
    "renewal_approaching": "qbr_value",
    "new_enterprise_customer": "sow_prerequisite",
    "deployment_started": "deployment_intelligence",
}


class CSOrchestrator:
    """Central orchestrator that routes events to the correct agent."""

    def __init__(self):
        self.memory_agent = CustomerMemoryAgent()
        self.agents: dict[str, BaseAgent] = {}
        self._register_agents()

    def _register_agents(self):
        """Instantiate all agents and register by name."""
        agent_classes = [
            HealthMonitorAgent,
            CallIntelAgent,
            TicketTriageAgent,
            TroubleshootAgent,
            EscalationAgent,
            QBRAgent,
            SOWAgent,
            DeploymentIntelAgent,
        ]
        for cls in agent_classes:
            agent = cls()
            self.agents[agent.agent_name] = agent

    def route(self, db_session, event: dict) -> dict:
        """
        Route an event to the correct agent.

        Args:
            db_session: Sync SQLAlchemy session
            event: Dict with event_type, payload, customer_id, source, etc.

        Returns:
            {"agent_name": str, "result": dict, "routed": bool}
        """
        event_type = event.get("event_type", "")
        customer_id = event.get("customer_id")
        agent_name = EVENT_ROUTING.get(event_type)

        if not agent_name:
            logger.warning(f"No agent route for event_type={event_type}")
            return {
                "agent_name": None,
                "result": {
                    "success": False,
                    "output": {"error": f"No agent registered for event type: {event_type}"},
                    "reasoning_summary": "Unroutable event type.",
                },
                "routed": False,
            }

        agent = self.agents.get(agent_name)
        if not agent:
            logger.error(f"Agent {agent_name} registered in routing but not instantiated")
            return {
                "agent_name": agent_name,
                "result": {
                    "success": False,
                    "output": {"error": f"Agent {agent_name} not available"},
                    "reasoning_summary": "Agent instance not found.",
                },
                "routed": False,
            }

        # Build customer memory if we have a customer_id
        customer_memory = {}
        if customer_id:
            customer_memory = self.memory_agent.build_memory(db_session, customer_id)

        # Execute the agent
        result = agent.run(db_session, event, customer_memory)

        logger.info(
            f"Routed {event_type} → {agent_name} | "
            f"success={result.get('success')} | customer={customer_id}"
        )

        return {
            "agent_name": agent_name,
            "result": result,
            "routed": True,
        }

    def get_agent(self, agent_name: str) -> BaseAgent | None:
        """Get an agent instance by name."""
        if agent_name == "customer_memory":
            return self.memory_agent
        return self.agents.get(agent_name)


# Singleton
orchestrator = CSOrchestrator()
