"""Marker transformation service for generating starter/solution snapshots."""

import re
from collections.abc import Mapping

from ..constants import SOLUTION, STARTER
from ..models import LinePart


class LabMarkerProcessor:
    """Transforms lab markers into starter or solution payload."""

    def __init__(
        self, starter_state: str = STARTER, solution_state: str = SOLUTION
    ) -> None:
        """Create a processor with configurable starter/solution state names."""
        self._starter_state = starter_state
        self._solution_state = solution_state
        self._start_marker = re.compile(
            r'^\s*#\s*<lab\s+id="(?P<id>[^"]+)"(?:\s+state="starter")?\s*>',
            re.IGNORECASE,
        )
        self._end_marker = re.compile(r"^\s*#\s*</lab>\s*$", re.IGNORECASE)
        self._hidden_payload = re.compile(r"^(?P<indent>\s*)#\|\s*(?P<content>.*)$")

    def transform(
        self,
        source: str,
        target_lab_id: str,
        target_variant: str,
        lab_order: Mapping[str, int],
    ) -> str:
        """Transform one source file according to the requested lab context."""
        target_lab_index = lab_order[target_lab_id]
        lines = self._split_lines(source)
        output: list[str] = []

        self._transform_range(
            lines, 0, len(lines), output, target_lab_index, target_variant, lab_order
        )

        return "".join(output)

    def _transform_range(
        self,
        lines: list[LinePart],
        start_index: int,
        end_index: int,
        output: list[str],
        target_lab_index: int,
        target_variant: str,
        lab_order: Mapping[str, int],
    ) -> None:
        """Walk lines in one range and append transformed output."""
        index = start_index
        while index < end_index:
            line = lines[index]
            marker = self._start_marker.match(line.content)
            if marker is None:
                if not self._hidden_payload.match(line.content):
                    output.append(line.original)
                index += 1
                continue

            block_lab_id = marker.group("id")
            selected_state = self._resolve_state(
                block_lab_id, target_lab_index, target_variant, lab_order
            )
            block_end_index = self._find_block_end(
                lines, index + 1, end_index, block_lab_id
            )

            if selected_state == self._starter_state:
                self._add_starter_payload(
                    lines,
                    index + 1,
                    block_end_index,
                    output,
                    target_lab_index,
                    target_variant,
                    lab_order,
                )
            else:
                self._transform_range(
                    lines,
                    index + 1,
                    block_end_index,
                    output,
                    target_lab_index,
                    target_variant,
                    lab_order,
                )

            index = block_end_index + 1

    def _add_starter_payload(
        self,
        lines: list[LinePart],
        start_index: int,
        end_index: int,
        output: list[str],
        target_lab_index: int,
        target_variant: str,
        lab_order: Mapping[str, int],
    ) -> None:
        """Extract starter payload while preserving nested block semantics."""
        index = start_index
        while index < end_index:
            marker = self._start_marker.match(lines[index].content)
            if marker is not None:
                block_lab_id = marker.group("id")
                block_end_index = self._find_block_end(
                    lines, index + 1, end_index, block_lab_id
                )
                selected_state = self._resolve_state(
                    block_lab_id,
                    target_lab_index,
                    target_variant,
                    lab_order,
                )

                if selected_state == self._starter_state:
                    self._add_starter_payload(
                        lines,
                        index + 1,
                        block_end_index,
                        output,
                        target_lab_index,
                        target_variant,
                        lab_order,
                    )
                else:
                    self._transform_range(
                        lines,
                        index + 1,
                        block_end_index,
                        output,
                        target_lab_index,
                        target_variant,
                        lab_order,
                    )

                index = block_end_index + 1
                continue

            if self._hidden_payload.match(lines[index].content):
                output.append(self._unwrap_lab_line(lines[index]))
            index += 1

    def _find_block_end(
        self, lines: list[LinePart], start_index: int, end_index: int, block_lab_id: str
    ) -> int:
        """Find the matching closing marker index for one opening marker."""
        depth = 0
        for index in range(start_index, end_index):
            if self._start_marker.match(lines[index].content):
                depth += 1
                continue

            if not self._end_marker.match(lines[index].content):
                continue

            if depth == 0:
                return index

            depth -= 1

        raise ValueError(f"Missing closing lab marker for block '{block_lab_id}'.")

    def _resolve_state(
        self,
        block_lab_id: str,
        target_lab_index: int,
        target_variant: str,
        lab_order: Mapping[str, int],
    ) -> str:
        """Resolve whether a block should render as starter or solution."""
        block_lab_index = lab_order.get(block_lab_id)
        if block_lab_index is None:
            return self._starter_state

        if block_lab_index == target_lab_index:
            return target_variant

        return (
            self._solution_state
            if block_lab_index < target_lab_index
            else self._starter_state
        )

    def _unwrap_lab_line(self, line: LinePart) -> str:
        """Remove '#|' wrapper while preserving indentation and line ending."""
        match = self._hidden_payload.match(line.content)
        if match is None:
            return line.original
        return f"{match.group('indent')}{match.group('content')}{line.ending}"

    def _split_lines(self, source: str) -> list[LinePart]:
        """Split source text into LinePart objects while keeping CRLF/LF endings."""
        lines: list[LinePart] = []
        start = 0
        length = len(source)

        while start < length:
            newline_index = source.find("\n", start)
            if newline_index < 0:
                remaining = source[start:]
                lines.append(LinePart(original=remaining, content=remaining, ending=""))
                break

            line_end = newline_index
            ending = "\n"
            if line_end > start and source[line_end - 1] == "\r":
                line_end -= 1
                ending = "\r\n"

            line_content = source[start:line_end]
            lines.append(
                LinePart(
                    original=source[start : newline_index + 1],
                    content=line_content,
                    ending=ending,
                )
            )
            start = newline_index + 1

        return lines
