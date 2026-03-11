from __future__ import annotations


class SkillsibleError(Exception):
    """Base package error."""


class ManifestError(SkillsibleError):
    """Raised when a manifest is invalid."""


class AdapterError(SkillsibleError):
    """Raised when an adapter cannot perform an action."""
