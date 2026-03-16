"""
Pluggable Trait System for CS Control Plane agents.

Traits inject domain-specific context and guidance into agent pipelines
at each stage (perceive, think, act, reflect, finalize).

Usage:
    from app.agents.traits import TraitRegistry
    traits = TraitRegistry.resolve(["pattern_recognition", "sla_awareness"])
"""

from app.agents.traits.base_trait import BaseTrait
from app.agents.traits.registry import TraitRegistry

# Import all trait modules to trigger @TraitRegistry.register decorators
from app.agents.traits import (  # noqa: F401
    confidence_scoring,
    customer_sentiment,
    deadline_tracking,
    delegation,
    pattern_recognition,
    quality_evaluation,
    risk_assessment,
    root_cause_analysis,
    sla_awareness,
    strategic_oversight,
    trend_analysis,
)

__all__ = ["BaseTrait", "TraitRegistry"]
