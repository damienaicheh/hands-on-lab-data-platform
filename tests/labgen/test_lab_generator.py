"""Unit tests for the LabGenerator service behavior."""

import logging
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from tools.labgen.models import LabDefinition, LabManifest
from tools.labgen.services.lab_generator import LabGenerator


class LabGeneratorTests(unittest.TestCase):
    """Covers error and transformation behavior in lab generation."""

    def test_generate_labs_returns_error_for_unknown_lab(self) -> None:
        manifest = LabManifest(labs=[LabDefinition(id="1")])
        generator = LabGenerator(
            marker_processor=Mock(),
            file_enumerator=Mock(),
            text_file_detector=Mock(),
            logger=logging.getLogger("test.lab_generator"),
        )

        stderr_capture = StringIO()
        with redirect_stderr(stderr_capture):
            exit_code = generator.generate_labs(Path("."), manifest, "999")

        self.assertEqual(1, exit_code)
        self.assertIn("Unknown lab: 999", stderr_capture.getvalue())

    def test_generate_lab_transforms_text_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository_root = Path(temp_dir)
            source_path = repository_root / "src" / "sample.py"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("input", encoding="utf-8")

            manifest = LabManifest(
                output_root="generated_labs",
                labs=[LabDefinition(id="1")],
            )

            marker_processor = Mock()
            marker_processor.transform.return_value = "transformed"

            file_enumerator = Mock()
            file_enumerator.enumerate.return_value = [source_path]

            text_file_detector = Mock()
            text_file_detector.is_text_file.return_value = True

            generator = LabGenerator(
                marker_processor=marker_processor,
                file_enumerator=file_enumerator,
                text_file_detector=text_file_detector,
                logger=logging.getLogger("test.lab_generator"),
            )

            generator.generate_lab(repository_root, manifest, manifest.labs[0])

            generated_path = (
                repository_root / "generated_labs" / "1" / "src" / "sample.py"
            )
            self.assertEqual("transformed", generated_path.read_text(encoding="utf-8"))
            marker_processor.transform.assert_called_once()


if __name__ == "__main__":
    unittest.main()
