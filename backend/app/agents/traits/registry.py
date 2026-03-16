"""
TraitRegistry — Singleton registry for trait classes.

Traits register themselves via the @TraitRegistry.register decorator.
The pipeline engine resolves trait names (from YAML profiles) to instances.

Usage:
    from app.agents.traits.registry import TraitRegistry

    @TraitRegistry.register
    class MyTrait(BaseTrait):
        name = "my_trait"
        ...

    # Later, resolve from YAML config:
    traits = TraitRegistry.resolve(["my_trait", "other_trait"])
"""

import logging

from app.agents.traits.base_trait import BaseTrait

logger = logging.getLogger("traits.registry")


class TraitRegistry:
    _traits: dict[str, type[BaseTrait]] = {}

    @classmethod
    def register(cls, trait_class: type[BaseTrait]) -> type[BaseTrait]:
        """
        Class decorator: register a trait by its .name attribute.

        @TraitRegistry.register
        class PatternRecognition(BaseTrait):
            name = "pattern_recognition"
        """
        name = getattr(trait_class, "name", "")
        if not name:
            raise ValueError(f"Trait class {trait_class.__name__} must define a 'name' attribute")
        cls._traits[name] = trait_class
        logger.debug(f"Registered trait: {name} → {trait_class.__name__}")
        return trait_class

    @classmethod
    def get(cls, name: str) -> BaseTrait | None:
        """Get a new instance of a trait by name. Returns None if not found."""
        trait_class = cls._traits.get(name)
        if trait_class is None:
            logger.warning(f"Trait not found: {name}")
            return None
        return trait_class()

    @classmethod
    def resolve(cls, names: list[str]) -> list[BaseTrait]:
        """
        Resolve a list of trait names to instantiated trait objects.
        Skips unknown trait names with a warning.
        """
        traits = []
        for name in names:
            trait = cls.get(name)
            if trait is not None:
                traits.append(trait)
        return traits

    @classmethod
    def available(cls) -> list[str]:
        """List all registered trait names."""
        return sorted(cls._traits.keys())

    @classmethod
    def reset(cls) -> None:
        """Clear all registrations. Useful for testing."""
        cls._traits.clear()
