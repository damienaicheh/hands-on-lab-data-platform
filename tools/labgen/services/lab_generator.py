"""Core application service responsible for lab snapshot generation."""

import logging
import shutil
import sys
from pathlib import Path

from ..constants import STARTER
from ..models import LabDefinition, LabManifest
from .file_enumerator import IncludedFileEnumerator
from .marker_processor import LabMarkerProcessor
from .text_file_detector import TextFileDetector


class LabGenerator:
    """Orchestrates listing labs and generating starter snapshots."""

    def __init__(
        self,
        marker_processor: LabMarkerProcessor,
        file_enumerator: IncludedFileEnumerator,
        text_file_detector: TextFileDetector,
        logger: logging.Logger,
        starter_variant: str = STARTER,
    ) -> None:
        self._marker_processor = marker_processor
        self._file_enumerator = file_enumerator
        self._text_file_detector = text_file_detector
        self._logger = logger
        self._starter_variant = starter_variant

    def list_labs(self, manifest: LabManifest) -> int:
        """Print all available lab ids declared in the manifest."""
        self._logger.info(
            "Listing labs",
            extra={
                "event": "lab_list_requested",
                "lab_count": len(manifest.labs),
            },
        )
        for lab in manifest.labs:
            print(lab.id)
        return 0

    def generate_labs(
        self, repository_root: Path, manifest: LabManifest, requested_lab_id: str | None
    ) -> int:
        """Generate one or all labs based on the optional requested id."""
        labs = (
            manifest.labs
            if requested_lab_id is None
            else [lab for lab in manifest.labs if lab.id == requested_lab_id]
        )
        if not labs:
            print(f"Unknown lab: {requested_lab_id}", file=sys.stderr)
            return 1

        self._logger.info(
            "Generating labs",
            extra={
                "event": "lab_generation_started",
                "requested_lab_id": requested_lab_id,
                "selected_lab_count": len(labs),
            },
        )

        if requested_lab_id is None:
            output_root = repository_root / manifest.output_root
            if output_root.exists():
                shutil.rmtree(output_root)

        for lab in labs:
            self.generate_lab(repository_root, manifest, lab)

        self._logger.info(
            "Labs generated",
            extra={
                "event": "lab_generation_completed",
                "selected_lab_count": len(labs),
            },
        )

        return 0

    def generate_lab(
        self, repository_root: Path, manifest: LabManifest, lab: LabDefinition
    ) -> None:
        """Generate one lab output directory by transforming included files."""
        output_root = repository_root / manifest.output_root / lab.id
        if output_root.exists():
            shutil.rmtree(output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        files = list(self._file_enumerator.enumerate(repository_root, manifest))
        lab_order = {entry.id: index for index, entry in enumerate(manifest.labs)}

        self._logger.info(
            "Generating single lab",
            extra={
                "event": "single_lab_generation_started",
                "lab_id": lab.id,
                "file_count": len(files),
            },
        )

        for source_path in files:
            relative_path = source_path.relative_to(repository_root)
            destination_path = output_root / relative_path
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            if self._text_file_detector.is_text_file(source_path):
                source = source_path.read_text(encoding="utf-8")
                transformed = self._marker_processor.transform(
                    source, lab.id, self._starter_variant, lab_order
                )
                destination_path.write_text(transformed, encoding="utf-8")
            else:
                shutil.copy2(source_path, destination_path)

        print(f"Generated {output_root.relative_to(repository_root)}")
        self._logger.info(
            "Single lab generated",
            extra={
                "event": "single_lab_generation_completed",
                "lab_id": lab.id,
                "output_root": str(output_root),
            },
        )
