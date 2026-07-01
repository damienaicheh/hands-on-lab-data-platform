import unittest

from tools.labgen.main import LabMarkerProcessor


class LabMarkerProcessorTests(unittest.TestCase):
    def test_transform_for_current_lab_keeps_starter_payload(self) -> None:
        source = (
            "before\n"
            "# <lab id=\"1\">\n"
            "#|starter_line\n"
            "solution_line\n"
            "# </lab>\n"
            "after\n"
        )

        transformed = LabMarkerProcessor.transform(source, "1", "starter", {"1": 0})

        self.assertEqual("before\nstarter_line\nafter\n", transformed)

    def test_transform_for_next_lab_keeps_previous_solution(self) -> None:
        source = (
            "# <lab id=\"1\">\n"
            "#|starter_line\n"
            "solution_line\n"
            "# </lab>\n"
            "# <lab id=\"2\">\n"
            "#|next_starter\n"
            "next_solution\n"
            "# </lab>\n"
        )

        transformed = LabMarkerProcessor.transform(source, "2", "starter", {"1": 0, "2": 1})

        self.assertEqual("solution_line\nnext_starter\n", transformed)


if __name__ == "__main__":
    unittest.main()
