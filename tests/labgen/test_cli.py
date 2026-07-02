"""Unit tests for LabGen CLI command dispatch and option handling."""

import logging
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.labgen.cli import LabGenApplication
from tools.labgen.models import LabDefinition, LabManifest


class StubRepositoryLocator:
    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root

    def find_root(self, start_path: Path) -> Path:
        return self.repository_root


class StubManifestLoader:
    def __init__(self, manifest: LabManifest) -> None:
        self.manifest = manifest
        self.last_path: Path | None = None

    def load(self, manifest_path: Path) -> LabManifest:
        self.last_path = manifest_path
        return self.manifest


class StubLabGenerator:
    def __init__(self) -> None:
        self.list_called_with: LabManifest | None = None
        self.generate_called_with: tuple[Path, LabManifest, str | None] | None = None

    def list_labs(self, manifest: LabManifest) -> int:
        self.list_called_with = manifest
        return 7

    def generate_labs(
        self, repository_root: Path, manifest: LabManifest, requested_lab_id: str | None
    ) -> int:
        self.generate_called_with = (repository_root, manifest, requested_lab_id)
        return 9


class LabGenApplicationTests(unittest.TestCase):
    """Verifies command parsing and dispatch behavior for the CLI layer."""

    def test_list_command_dispatches_to_generator(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository_root = Path(temp_dir)
            docs_dir = repository_root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "manifest.json").write_text("{}", encoding="utf-8")

            manifest = LabManifest(labs=[LabDefinition(id="1")])
            app = LabGenApplication(
                StubRepositoryLocator(repository_root),
                StubManifestLoader(manifest),
                StubLabGenerator(),
                logging.getLogger("test.labgen.cli"),
            )

            exit_code = app.run(["list"])

            self.assertEqual(7, exit_code)

    def test_generate_is_default_command(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository_root = Path(temp_dir)
            docs_dir = repository_root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "manifest.json").write_text("{}", encoding="utf-8")

            manifest = LabManifest(labs=[LabDefinition(id="1")])
            generator = StubLabGenerator()
            app = LabGenApplication(
                StubRepositoryLocator(repository_root),
                StubManifestLoader(manifest),
                generator,
                logging.getLogger("test.labgen.cli"),
            )

            exit_code = app.run([])

            self.assertEqual(9, exit_code)
            self.assertIsNotNone(generator.generate_called_with)
            generated_root, generated_manifest, requested_lab_id = (
                generator.generate_called_with
            )
            self.assertEqual(repository_root, generated_root)
            self.assertEqual(manifest, generated_manifest)
            self.assertIsNone(requested_lab_id)

    def test_generate_variant_option_returns_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository_root = Path(temp_dir)
            docs_dir = repository_root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "manifest.json").write_text("{}", encoding="utf-8")

            manifest = LabManifest(labs=[LabDefinition(id="1")])
            generator = StubLabGenerator()
            app = LabGenApplication(
                StubRepositoryLocator(repository_root),
                StubManifestLoader(manifest),
                generator,
                logging.getLogger("test.labgen.cli"),
            )

            stderr_capture = StringIO()
            with redirect_stderr(stderr_capture):
                exit_code = app.run(["generate", "--variant", "solution"])

            self.assertEqual(1, exit_code)
            self.assertIn("--variant is no longer supported", stderr_capture.getvalue())
            self.assertIsNone(generator.generate_called_with)


if __name__ == "__main__":
    unittest.main()
