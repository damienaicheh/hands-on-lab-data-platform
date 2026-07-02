"""Command-line interface orchestration for LabGen."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from .services.lab_generator import LabGenerator
from .services.manifest_loader import ManifestLoader
from .services.repository_locator import RepositoryLocator


class LabGenApplication:
    """Coordinates argument parsing and dispatch to domain services."""

    def __init__(
        self,
        repository_locator: RepositoryLocator,
        manifest_loader: ManifestLoader,
        lab_generator: LabGenerator,
        logger: logging.Logger,
    ) -> None:
        self._repository_locator = repository_locator
        self._manifest_loader = manifest_loader
        self._lab_generator = lab_generator
        self._logger = logger

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Execute one CLI command and return a process-style exit code."""
        args = list(argv) if argv is not None else sys.argv[1:]
        if not args:
            args = ["generate"]

        parser = self._build_parser()
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 1

        if parsed_args.verbose:
            self._logger.setLevel(logging.INFO)

        self._logger.info(
            "Command parsed",
            extra={
                "event": "cli_command_parsed",
                "command": parsed_args.command,
            },
        )

        repository_root = self._repository_locator.find_root(Path.cwd())
        manifest_path = repository_root / "docs" / "manifest.json"

        if not manifest_path.exists():
            print(
                f"Missing manifest: {manifest_path.relative_to(repository_root)}",
                file=sys.stderr,
            )
            return 1

        manifest = self._manifest_loader.load(manifest_path)

        if parsed_args.command == "list":
            return self._lab_generator.list_labs(manifest)

        if parsed_args.command == "generate":
            if parsed_args.variant is not None:
                print(
                    "--variant is no longer supported. LabGen now generates one starter snapshot per lab.",
                    file=sys.stderr,
                )
                return 1
            return self._lab_generator.generate_labs(
                repository_root, manifest, parsed_args.lab
            )

        return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        """Create the CLI parser with all supported LabGen commands."""
        parser = argparse.ArgumentParser(
            prog="python -m tools.labgen", description="Generate lab starter snapshots"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable informational structured logs",
        )

        subparsers = parser.add_subparsers(dest="command")
        subparsers.required = True

        subparsers.add_parser("list", help="List labs from docs/manifest.json")
        generate_parser = subparsers.add_parser(
            "generate", help="Generate starter snapshots"
        )
        generate_parser.add_argument(
            "--lab", dest="lab", help="Generate only one lab by id"
        )
        generate_parser.add_argument(
            "--variant", dest="variant", help="Deprecated option"
        )

        return parser
