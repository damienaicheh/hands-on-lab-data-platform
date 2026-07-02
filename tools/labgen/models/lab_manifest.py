"""Domain model describing all LabGen configuration loaded from manifest.json."""

from dataclasses import dataclass, field

from .lab_definition import LabDefinition


@dataclass(frozen=True)
class LabManifest:
    """Immutable manifest payload used during generation."""

    output_root: str = "generated/labs"
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    labs: list[LabDefinition] = field(default_factory=lambda: [LabDefinition(id="1")])
