"""
Orchestrator (Naveen Kapoor) — Routes events directly to specialist agents.

The primary entry point is route_direct() in event_service.py which uses
EVENT_ROUTING to dispatch events to specialists. The Orchestrator class
provides a legacy route() method that builds customer memory and runs the
specialist through the pipeline.
"""

import json
import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.agents.memory_agent import CustomerMemoryAgent

logger = logging.getLogger("agents.orchestrator")

# Event type → specialist agent (primary routing table)
EVENT_ROUTING = {
    "jira_ticket_created": "triage_agent",
    "jira_ticket_updated": "triage_agent",
    "ticket_escalated": "escalation_summary",
    "support_bundle_uploaded": "troubleshooter",
    "daily_health_check": "health_monitor",
    "manual_health_check": "health_monitor",
    "renewal_approaching": "qbr_value",
    "new_enterprise_customer": "sow_prerequisite",
    "deployment_started": "deployment_intelligence",
    # HubSpot deal events
    "deal_stage_changed": "presales_funnel",
    "new_customer": "sow_prerequisite",
    # User chat events
    "user_chat_fathom": "health_monitor",
    "user_chat_health": "health_monitor",
    "user_chat_ticket": "triage_agent",
    "user_chat_deal": "presales_funnel",
    "user_chat_general": "health_monitor",
}

# Event type → lane name (for context/logging only)
EVENT_LANE_MAP = {
    "jira_ticket_created": ["support"],
    "jira_ticket_updated": ["support"],
    "ticket_escalated": ["support"],
    "support_bundle_uploaded": ["support"],
    "daily_health_check": ["value"],
    "manual_health_check": ["value"],
    "renewal_approaching": ["value"],
    "new_enterprise_customer": ["delivery"],
    "deployment_started": ["delivery"],
    "deal_stage_changed": ["presales"],
    "new_customer": ["delivery"],
    "user_chat_fathom": ["value"],
    "user_chat_health": ["value"],
    "user_chat_ticket": ["support"],
    "user_chat_deal": ["presales"],
    "user_chat_general": ["value", "support"],
}


class Orchestrator(BaseAgent):
    """Routes events directly to specialist agents by event type."""

    agent_id = "cso_orchestrator"

    def __init__(self):
        super().__init__()
        self._memory_agent = CustomerMemoryAgent()

    def perceive(self, task: dict) -> dict:
        self.memory.set_context("event_type", task.get("event_type", ""))
        self.memory.set_context("customer_id", task.get("customer_id"))
        self.memory.set_context("description", task.get("description", ""))
        self.memory.set_context("priority", task.get("priority", 5))
        return task

    def retrieve(self, task: dict) -> dict:
        context = self.memory.assemble_context(task.get("description", ""))
        customer_memory = task.get("customer_memory", {})
        if not customer_memory and task.get("customer_id") and self._current_db:
            customer_memory = self._memory_agent.build_memory(
                self._current_db, task["customer_id"]
            )
            task["customer_memory"] = customer_memory
        context["customer_memory"] = customer_memory
        return context

    def think(self, task: dict, context: dict) -> dict:
        """Determine which specialist should handle this event."""
        event_type = task.get("event_type", "")
        agent_id = EVENT_ROUTING.get(event_type)

        if agent_id and AgentFactory.is_registered(agent_id):
            return {
                "specialist": agent_id,
                "priority": task.get("priority", 5),
                "rationale": f"Routing {event_type} to {agent_id}",
            }

        # Fallback: ask Claude to pick a specialist
        user_message = self._build_routing_prompt(task, context)
        response = self._call_claude(user_message, max_tokens=1024, temperature=0.2)
        parsed = self._parse_claude(response)

        if "error" in parsed:
            return {
                "specialist": "health_monitor",
                "priority": task.get("priority", 5),
                "rationale": "Fallback routing",
            }
        return parsed

    def _is_chat_event(self, event_type: str) -> bool:
        return event_type.startswith("user_chat_")

    def act(self, task: dict, thinking: dict) -> dict:
        """Route directly to the specialist agent."""
        agent_id = thinking.get("specialist", EVENT_ROUTING.get(task.get("event_type", ""), "health_monitor"))
        event_type = task.get("event_type", "")
        is_chat = self._is_chat_event(event_type)

        print(f"[Orchestrator | Naveen Kapoor] act() -- routing to specialist={agent_id} is_chat={is_chat}", flush=True)
        logger.info(f"[Orchestrator] Routing: event_type={event_type}, specialist={agent_id}")

        if not AgentFactory.is_registered(agent_id):
            return {"success": False, "error": f"Specialist '{agent_id}' not registered"}

        specialist = AgentFactory.create(agent_id)

        try:
            result = specialist.run(
                self._current_db, task, task.get("customer_memory"),
            )
            return {"specialist_result": result, "specialist": agent_id}
        except Exception as e:
            if is_chat:
                logger.warning(f"[Orchestrator] Specialist '{agent_id}' failed (non-fatal for chat): {e}")
                return {
                    "specialist_result": {"success": False, "error": str(e)},
                    "specialist": agent_id,
                }
            raise

    def finalize(self, task: dict, result: dict) -> dict:
        """Pass through the specialist result."""
        specialist_result = result.get("specialist_result", {})
        if not specialist_result:
            return {
                "success": False,
                "error": "No specialist output",
                "reasoning_summary": "No specialist produced output.",
            }
        return {
            "success": specialist_result.get("success", False),
            "output": specialist_result.get("output", specialist_result),
            "specialist": result.get("specialist", ""),
            "reasoning_summary": specialist_result.get("reasoning_summary", "Event processed."),
        }

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_routing_prompt(self, task: dict, context: dict) -> str:
        customer_memory = context.get("customer_memory", {})
        customer = customer_memory.get("customer", {})
        description = task.get("description", "")
        event_type = task.get("event_type", "")

        parts = [
            "## Incoming Event",
            f"Event Type: {event_type}",
            f"Description: {description[:1000]}",
            "",
            "## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Health: {customer_memory.get('health', {}).get('current_score', 'N/A')}",
            f"Open Tickets: {customer_memory.get('tickets', {}).get('open_count', 0)}",
            "",
            "## Available Specialists",
            "- triage_agent: Ticket classification, severity, diagnostics (Support lane)",
            "- troubleshooter: Root cause analysis from support bundles (Support lane)",
            "- escalation_summary: Escalation document compilation (Support lane)",
            "- health_monitor: Customer health scoring and risk flags (Value lane)",
            "- qbr_value: Quarterly business review generation (Value lane)",
            "- sow_prerequisite: SOW docs and onboarding checklists (Delivery lane)",
            "- deployment_intelligence: Deployment validation (Delivery lane)",
            "",
            "## Instructions",
            "Choose the best specialist for this event.",
            'Return JSON: {"specialist": "agent_id", "priority": 1-10, "rationale": "..."}',
        ]
        return "\n".join(parts)

    def _fallback_routing(self, task: dict) -> dict:
        """Event-type based routing when Claude planning fails."""
        event_type = task.get("event_type", "")
        agent_id = EVENT_ROUTING.get(event_type, "health_monitor")
        return {
            "specialist": agent_id,
            "priority": task.get("priority", 5),
            "rationale": f"Fallback routing for {event_type}",
        }

    # ── Legacy Compatibility ─────────────────────────────────────────

    def route(self, db_session, event: dict) -> dict:
        """
        Legacy route() interface — builds customer memory and runs the
        specialist through the pipeline.
        """
        event_type = event.get("event_type", "")
        customer_id = event.get("customer_id")
        print(f"\n[Orchestrator | Naveen Kapoor] ===============================", flush=True)
        print(f"[Orchestrator] route() event_type={event_type} customer_id={customer_id}", flush=True)

        # Build customer memory
        customer_memory = {}
        if customer_id:
            customer_memory = self._memory_agent.build_memory(db_session, customer_id)
        else:
            customer_memory = self._memory_agent.build_portfolio_memory(db_session)

        result = self.run(db_session, event, customer_memory)

        specialist_name = EVENT_ROUTING.get(event_type, self.agent_id)

        # Extract specialist result from pipeline output
        specialist_result = result
        output = result.get("output", {}) if isinstance(result, dict) else {}
        if isinstance(output, dict):
            specialist_result = output.get("specialist_result", output)

        print(f"[Orchestrator] route() done: specialist={specialist_name}, success={result.get('success')}", flush=True)
        print(f"[Orchestrator] ===============================\n", flush=True)

        return {
            "agent_name": specialist_name,
            "result": specialist_result,
            "orchestrator_result": result,
            "routed": True,
        }

    def get_agent(self, agent_name: str):
        """Legacy: get an agent instance by name."""
        if agent_name == "customer_memory":
            return self._memory_agent
        if AgentFactory.is_registered(agent_name):
            return AgentFactory.create(agent_name)
        return None


# Singleton for backward compat
orchestrator = Orchestrator()

AgentFactory.register("cso_orchestrator", Orchestrator)
