"""Unit tests for marker processing and glob matching primitives."""

import unittest
from pathlib import Path

from tools.labgen.constants import STARTER
from tools.labgen.services.glob_matcher import GlobMatcher
from tools.labgen.services.marker_processor import LabMarkerProcessor
from tools.labgen.services.text_file_detector import TextFileDetector


class LabMarkerProcessorTests(unittest.TestCase):
    """Validates transformation and pattern matching core logic."""

    def test_transform_for_current_lab_keeps_starter_payload(self) -> None:
        processor = LabMarkerProcessor()
        source = (
            'before\n# <lab id="1">\n#|starter_line\nsolution_line\n# </lab>\nafter\n'
        )

        transformed = processor.transform(source, "1", STARTER, {"1": 0})

        self.assertEqual("before\nstarter_line\nafter\n", transformed)

    def test_transform_for_next_lab_keeps_previous_solution(self) -> None:
        processor = LabMarkerProcessor()
        source = (
            '# <lab id="1">\n'
            "#|starter_line\n"
            "solution_line\n"
            "# </lab>\n"
            '# <lab id="2">\n'
            "#|next_starter\n"
            "next_solution\n"
            "# </lab>\n"
        )

        transformed = processor.transform(source, "2", STARTER, {"1": 0, "2": 1})

        self.assertEqual("solution_line\nnext_starter\n", transformed)

    def test_glob_match_supports_double_wildcard(self) -> None:
        matcher = GlobMatcher()

        self.assertTrue(matcher.is_match("src/agents/main.py", "src/**"))
        self.assertTrue(matcher.is_match("src/agents/main.py", "src/**/*.py"))
        self.assertFalse(matcher.is_match("infra/main.tf", "src/**"))

    def test_text_file_detector_defaults_to_python_only(self) -> None:
        detector = TextFileDetector()

        self.assertTrue(detector.is_text_file(Path("src/agents/main.py")))
        self.assertFalse(detector.is_text_file(Path("README.md")))

    def test_text_file_detector_accepts_custom_extensions(self) -> None:
        detector = TextFileDetector({".py", ".md"})

        self.assertTrue(detector.is_text_file(Path("README.md")))

    def test_transform_handles_nested_starter_blocks(self) -> None:
        processor = LabMarkerProcessor()
        source = (
            "before\n"
            '# <lab id="1">\n'
            "#|outer_todo\n"
            "outer_solution\n"
            '# <lab id="2">\n'
            "#|inner_todo\n"
            "inner_solution\n"
            "# </lab>\n"
            "# </lab>\n"
            "after\n"
        )

        transformed = processor.transform(source, "1", STARTER, {"1": 0, "2": 1})

        self.assertEqual("before\nouter_todo\ninner_todo\nafter\n", transformed)

    def test_transform_handles_nested_current_lab_inside_previous_solution(
        self,
    ) -> None:
        processor = LabMarkerProcessor()
        source = (
            "before\n"
            '# <lab id="1">\n'
            "#|outer_todo\n"
            "outer_solution\n"
            '# <lab id="2">\n'
            "#|inner_todo\n"
            "inner_solution\n"
            "# </lab>\n"
            "outer_after\n"
            "# </lab>\n"
            "after\n"
        )

        transformed = processor.transform(source, "2", STARTER, {"1": 0, "2": 1})

        self.assertEqual(
            "before\nouter_solution\ninner_todo\nouter_after\nafter\n",
            transformed,
        )

    def test_transform_handles_nested_unknown_lab_id_as_starter(self) -> None:
        processor = LabMarkerProcessor()
        source = (
            '# <lab id="1">\n'
            "#|outer_todo\n"
            '# <lab id="2">\n'
            "#|inner_todo\n"
            "inner_solution\n"
            "# </lab>\n"
            "outer_solution\n"
            "# </lab>\n"
        )

        transformed = processor.transform(source, "1", STARTER, {"1": 0})

        self.assertEqual("outer_todo\ninner_todo\n", transformed)


if __name__ == "__main__":
    unittest.main()
