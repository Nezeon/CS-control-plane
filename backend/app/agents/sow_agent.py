"""
SOW & Prerequisite Agent — Tier 3 Specialist (Delivery Lane).

Generates pre-deployment checklists and SOW validation.
Reports to: Priya Mehta (delivery_lead)
Traits: deadline_tracking, risk_assessment
"""

import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent

logger = logging.getLogger("agents.sow")


class SOWAgent(BaseAgent):
    """Generates pre-deployment checklists and SOW validation."""

    agent_id = "sow_prerequisite"

    def perceive(self, task: dict) -> dict:
        customer = task.get("customer_memory", {}).get("customer", {})
        if not customer.get("name"):
            raise ValueError("No customer context available")

        self.memory.set_context("customer_name", customer.get("name"))
        self.memory.set_context("deployment_mode", customer.get("deployment_mode"))
        self.memory.set_context("integrations", customer.get("integrations", []))
        return task

    def retrieve(self, task: dict) -> dict:
        customer_name = task.get("customer_name", "unknown")
        context = self.memory.assemble_context(
            f"deployment prerequisites for {customer_name}"
        )
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        customer = context.get("customer_memory", {}).get("customer", {})
        user_message = self._build_prompt(customer)

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Deployment Experience\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=4000, temperature=0.2)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}
        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("reasoning", "SOW prerequisites generated."),
        }

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_prompt(self, customer: dict) -> str:
        parts = [
            "## New Enterprise Customer Deployment",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')}",
            f"Tier: {customer.get('tier', 'N/A')}",
            "",
            "## Deployment Configuration",
            f"Deployment Mode: {customer.get('deployment_mode', 'N/A')}",
            f"Product Version: {customer.get('product_version', 'N/A')}",
            "",
            "## Integrations Required",
        ]

        integrations = customer.get("integrations", [])
        if integrations:
            for i in integrations:
                parts.append(f"  - {i}")
        else:
            parts.append("  None specified")

        parts.extend(["", "## Known Constraints"])
        constraints = customer.get("known_constraints", [])
        if constraints:
            for c in constraints:
                parts.append(f"  - {c}")
        else:
            parts.append("  None specified")

        return "\n".join(parts)


AgentFactory.register("sow_prerequisite", SOWAgent)
