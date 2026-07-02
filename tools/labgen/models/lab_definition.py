"""Domain model for one lab entry declared in the manifest."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LabDefinition:
    """Identifies one generated lab snapshot by id."""

    id: str
