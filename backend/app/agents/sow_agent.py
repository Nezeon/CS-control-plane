import logging

from app.agents.base_agent import BaseAgent
from app.services import claude_service

logger = logging.getLogger("agents.sow_prerequisite")

SOW_SYSTEM_PROMPT = """You are a SOW & Prerequisite Agent for a cybersecurity SaaS company (HivePro).
Analyze the customer's deployment configuration and generate a pre-deployment checklist.

Return ONLY valid JSON (no markdown fences):
{
  "prerequisites": [
    {"item": "<prerequisite>", "category": "<network|security|infrastructure|access>", "critical": <true|false>}
  ],
  "integration_checklist": [
    {"integration": "<integration name>", "steps": ["<step 1>", "<step 2>"], "estimated_hours": <float>}
  ],
  "network_requirements": {
    "ports": ["<port/protocol>"],
    "bandwidth": "<minimum bandwidth>",
    "connectivity": "<connectivity requirements>"
  },
  "security_requirements": ["<requirement 1>", "<requirement 2>"],
  "estimated_deployment_timeline": {
    "total_days": <int>,
    "phases": [
      {"phase": "<phase name>", "days": <int>, "description": "<what happens>"}
    ]
  },
  "risk_assessment": [
    {"risk": "<risk description>", "severity": "<high|medium|low>", "mitigation": "<mitigation strategy>"}
  ],
  "recommended_deployment_plan": "<paragraph with deployment approach>",
  "reasoning": "<2-3 sentence explanation>"
}"""


class SOWAgent(BaseAgent):
    """Generates pre-deployment checklists and SOW validation."""

    agent_name = "sow_prerequisite"
    agent_type = "delivery"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        customer = customer_memory.get("customer", {})
        if not customer.get("name"):
            return {
                "success": False,
                "output": {"error": "No customer context available"},
                "reasoning_summary": "Customer memory is empty.",
            }

        user_message = self._build_prompt(customer)

        response = claude_service.generate_sync(
            system_prompt=SOW_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=4000,
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
            "reasoning_summary": parsed.get("reasoning", "SOW prerequisites generated."),
        }

    def _build_prompt(self, customer: dict) -> str:
        parts = [
            f"## New Enterprise Customer Deployment",
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

        parts.extend([
            "",
            "## Known Constraints",
        ])
        constraints = customer.get("known_constraints", [])
        if constraints:
            for c in constraints:
                parts.append(f"  - {c}")
        else:
            parts.append("  None specified")

        return "\n".join(parts)
