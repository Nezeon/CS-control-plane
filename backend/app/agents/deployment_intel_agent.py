import logging

from app.agents.base_agent import BaseAgent
from app.services import claude_service, rag_service

logger = logging.getLogger("agents.deployment_intelligence")

DEPLOYMENT_INTEL_SYSTEM_PROMPT = """You are a Deployment Intelligence Agent for a cybersecurity SaaS company (HivePro).
Analyze the customer's deployment configuration and known issues from similar deployments.
Provide guidance for a successful deployment.

Return ONLY valid JSON (no markdown fences):
{
  "known_issues": [
    {"issue": "<known issue>", "severity": "<high|medium|low>", "workaround": "<workaround if available>"}
  ],
  "configuration_recommendations": [
    {"setting": "<config setting>", "recommended_value": "<value>", "reason": "<why>"}
  ],
  "compatibility_notes": ["<note 1>", "<note 2>"],
  "monitoring_setup_guide": {
    "key_metrics": ["<metric 1>", "<metric 2>"],
    "alert_thresholds": [
      {"metric": "<metric>", "threshold": "<value>", "action": "<what to do>"}
    ]
  },
  "post_deployment_verification_steps": [
    {"step": 1, "check": "<what to verify>", "expected_result": "<what success looks like>"}
  ],
  "reasoning": "<2-3 sentence explanation>"
}"""


class DeploymentIntelAgent(BaseAgent):
    """Provides deployment guidance based on known issues for the customer's config."""

    agent_name = "deployment_intelligence"
    agent_type = "delivery"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        customer = customer_memory.get("customer", {})
        if not customer.get("name"):
            return {
                "success": False,
                "output": {"error": "No customer context available"},
                "reasoning_summary": "Customer memory is empty.",
            }

        # Use RAG to find known issues for similar deployments
        deployment_query = (
            f"{customer.get('deployment_mode', '')} "
            f"{customer.get('product_version', '')} "
            f"{' '.join(customer.get('integrations', []))}"
        )
        similar_problems = rag_service.find_similar_problems(deployment_query, n_results=5)

        user_message = self._build_prompt(customer, similar_problems)

        response = claude_service.generate_sync(
            system_prompt=DEPLOYMENT_INTEL_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=3000,
            temperature=0.2,
        )

        if "error" in response:
            return {
                "success": False,
                "output": response,
                "reasoning_summary": f"Claude API error: {response.get('detail', response.get('error'))}",
            }

        parsed = claude_service.parse_json_response(response["content"])
        if "error" in parsed and parsed["error"] == "parse_failed":
            return {
                "success": False,
                "output": {"error": "Failed to parse response", "raw": response["content"][:500]},
                "reasoning_summary": "Claude returned unparseable response.",
            }

        return {
            "success": True,
            "output": parsed,
            "reasoning_summary": parsed.get("reasoning", "Deployment intelligence generated."),
        }

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
