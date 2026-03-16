"""
Deployment Intelligence Agent — Tier 3 Specialist (Delivery Lane).

Provides deployment guidance based on known issues for the customer's config.
Reports to: Priya Mehta (delivery_lead)
Traits: risk_assessment, pattern_recognition
"""

import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.services import rag_service

logger = logging.getLogger("agents.deployment_intel")


class DeploymentIntelAgent(BaseAgent):
    """Provides deployment guidance based on known issues for similar configs."""

    agent_id = "deployment_intelligence"

    def perceive(self, task: dict) -> dict:
        customer = task.get("customer_memory", {}).get("customer", {})
        if not customer.get("name"):
            raise ValueError("No customer context available")

        self.memory.set_context("customer_name", customer.get("name"))
        self.memory.set_context("deployment_mode", customer.get("deployment_mode"))
        self.memory.set_context("product_version", customer.get("product_version"))
        return task

    def retrieve(self, task: dict) -> dict:
        customer = task.get("customer_memory", {}).get("customer", {})

        # RAG: known issues for similar deployments
        deployment_query = (
            f"{customer.get('deployment_mode', '')} "
            f"{customer.get('product_version', '')} "
            f"{' '.join(customer.get('integrations', []))}"
        )
        similar_problems = rag_service.find_similar_problems(deployment_query, n_results=5)
        self.memory.set_context("similar_problems", similar_problems)

        # Episodic + semantic memory
        context = self.memory.assemble_context(deployment_query)
        context["similar_problems"] = similar_problems
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        customer = context.get("customer_memory", {}).get("customer", {})
        similar_problems = context.get("similar_problems", [])

        user_message = self._build_prompt(customer, similar_problems)

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Deployment Intelligence\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=3000, temperature=0.2)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}
        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("reasoning", "Deployment intelligence generated."),
        }

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_prompt(self, customer: dict, similar_problems: list) -> str:
        parts = [
            "## Deployment Configuration",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')}",
            f"Deployment Mode: {customer.get('deployment_mode', 'N/A')}",
            f"Product Version: {customer.get('product_version', 'N/A')}",
            f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
            f"Known Constraints: {', '.join(customer.get('known_constraints', [])) or 'None'}",
        ]

        if similar_problems:
            parts.extend(["", "## Known Issues from Similar Deployments (vector search)"])
            for sp in similar_problems[:5]:
                sim = sp.get("similarity", 0)
                parts.append(f"  - [similarity={sim:.2f}] {sp.get('text', 'N/A')[:200]}")
        else:
            parts.append("\n## No known issues found for similar deployments.")

        return "\n".join(parts)


AgentFactory.register("deployment_intelligence", DeploymentIntelAgent)
