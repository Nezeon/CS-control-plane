"""
Delegation trait — Injects available agent roster and expertise for task assignment.

Used by: cso_orchestrator
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry


@TraitRegistry.register
class Delegation(BaseTrait):
    name = "delegation"
    description = "Provides agent roster and expertise context for effective task delegation"

    def on_perceive(self, context: dict) -> str:
        # Build available agents roster from ProfileLoader
        roster_lines = []
        try:
            from app.agents.profile_loader import ProfileLoader
            loader = ProfileLoader.get()
            agent_id = context.get("agent_id", "")
            manages = loader.get_manages(agent_id)

            for managed_id in manages:
                profile = loader.get_agent_profile(managed_id)
                if profile:
                    name = profile.get("name", managed_id)
                    role = profile.get("role", "")
                    expertise = ", ".join(profile.get("expertise", [])[:3])
                    roster_lines.append(f"  - {name} ({managed_id}): {role}. Expertise: {expertise}")
        except Exception:
            pass

        if roster_lines:
            roster = "\n".join(roster_lines)
            return f"AVAILABLE AGENTS FOR DELEGATION:\n{roster}"

        return "DELEGATION: Consider which team members should handle subtasks based on their expertise."

    def on_think(self, task: str, context: dict) -> str:
        return (
            "Identify which specialist(s) should handle each subtask based on their expertise. "
            "Assign clear, specific instructions. Avoid overloading a single specialist."
        )
