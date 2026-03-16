"""
Quality Evaluation trait — Checks output completeness and quality.

Used by: cso_orchestrator (T1), support_lead (T2)
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry

REQUIRED_FIELDS = {"summary", "confidence"}
RECOMMENDED_FIELDS = {"action_items", "reasoning"}


@TraitRegistry.register
class QualityEvaluation(BaseTrait):
    name = "quality_evaluation"
    description = "Validates output completeness: checks for required fields, flags gaps"

    def on_act_postprocess(self, result: dict, context: dict) -> dict:
        missing = []
        for field in REQUIRED_FIELDS:
            if field not in result or not result[field]:
                missing.append(field)

        recommended_missing = []
        for field in RECOMMENDED_FIELDS:
            if field not in result or not result[field]:
                recommended_missing.append(field)

        if missing or recommended_missing:
            result["quality_flags"] = {
                "missing_required": missing,
                "missing_recommended": recommended_missing,
                "quality_pass": len(missing) == 0,
            }

        return result

    def on_reflect(self, result: dict, context: dict) -> str:
        return (
            "Evaluate output completeness: Are all deliverables present? "
            "Is the reasoning transparent and well-supported? "
            "Are action items specific, assignable, and time-bound? "
            "Would a human reviewer find this output immediately actionable?"
        )
