"""Manifest loading service for translating JSON into domain models."""

import json
from pathlib import Path

from ..models import LabDefinition, LabManifest


class ManifestLoader:
    """Loads docs/manifest.json into a strongly typed LabManifest."""

    def load(self, manifest_path: Path) -> LabManifest:
        """Read and parse one manifest file from disk."""
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_labs = data.get("labs", [])
        labs = [
            LabDefinition(
                id=str(item["id"]),
            )
            for item in raw_labs
        ]

        if not labs:
            labs = [LabDefinition(id="1")]

        return LabManifest(
            output_root=str(data.get("outputRoot", "generated/labs")),
            include=[str(item) for item in data.get("include", [])],
            exclude=[str(item) for item in data.get("exclude", [])],
            labs=labs,
        )
