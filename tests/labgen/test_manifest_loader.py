"""Unit tests for manifest loading and defaulting behavior."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.labgen.services.manifest_loader import ManifestLoader


class ManifestLoaderTests(unittest.TestCase):
    """Validates how LabManifest is built from JSON data."""

    def test_load_defaults_to_lab_1_when_labs_is_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "outputRoot": "generated_labs",
                        "include": ["src/**"],
                        "exclude": ["generated_labs/**"],
                    }
                ),
                encoding="utf-8",
            )

            manifest = ManifestLoader().load(manifest_path)

            self.assertEqual(["1"], [lab.id for lab in manifest.labs])

    def test_load_defaults_to_lab_1_when_labs_is_empty(self) -> None:
        with TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "outputRoot": "generated_labs",
                        "include": ["src/**"],
                        "exclude": ["generated_labs/**"],
                        "labs": [],
                    }
                ),
                encoding="utf-8",
            )

            manifest = ManifestLoader().load(manifest_path)

            self.assertEqual(["1"], [lab.id for lab in manifest.labs])

    def test_load_uses_declared_labs_when_present(self) -> None:
        with TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "outputRoot": "generated_labs",
                        "include": ["src/**"],
                        "exclude": ["generated_labs/**"],
                        "labs": [{"id": "1"}, {"id": "2"}],
                    }
                ),
                encoding="utf-8",
            )

            manifest = ManifestLoader().load(manifest_path)

            self.assertEqual(["1", "2"], [lab.id for lab in manifest.labs])


if __name__ == "__main__":
    unittest.main()
