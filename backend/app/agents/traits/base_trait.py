"""
BaseTrait — Abstract base class for all agent traits.

Traits are pluggable behaviors that inject context and guidance into an agent's
pipeline at specific stages. Each trait defines 5 lifecycle hooks corresponding
to pipeline stage types: perceive, think, act, reflect, finalize.

Traits do NOT call the Claude API themselves — they return strings that the
pipeline engine collects and includes in the agent's prompt.
"""

import logging
from abc import ABC

logger = logging.getLogger("traits")


class BaseTrait(ABC):
    """Base class for all agent traits."""

    name: str = ""
    description: str = ""

    def on_perceive(self, context: dict) -> str:
        """
        Inject extra context before the agent perceives its task.
        Fires during the 'perceive' pipeline stage.

        Args:
            context: Agent context dict (agent_id, tier, lane, event, working_memory, etc.)

        Returns:
            Additional context string to append to the perception prompt.
        """
        return ""

    def on_think(self, task: str, context: dict) -> str:
        """
        Inject guidance into the agent's thinking stage.
        Fires during the 'think' pipeline stage.

        Args:
            task: The task description the agent is reasoning about.
            context: Agent context dict.

        Returns:
            Additional guidance string to append to the thinking prompt.
        """
        return ""

    def on_act_postprocess(self, result: dict, context: dict) -> dict:
        """
        Post-process the agent's action output.
        Fires after the 'act' pipeline stage completes.

        Args:
            result: The agent's output dict from the act stage.
            context: Agent context dict.

        Returns:
            Modified result dict (may add metadata fields like quality_flags, risk_level, etc.)
        """
        return result

    def on_reflect(self, result: dict, context: dict) -> str:
        """
        Add guidance to the agent's self-reflection.
        Fires during the 'reflect' pipeline stage.

        Args:
            result: The agent's output dict from execution.
            context: Agent context dict.

        Returns:
            Additional reflection guidance string.
        """
        return ""

    def on_complete(self, result: dict, context: dict) -> None:
        """
        Called when the agent's pipeline completes. Side effects OK.
        Fires after the 'finalize' stage or at pipeline end.

        Args:
            result: The final output dict.
            context: Agent context dict.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
