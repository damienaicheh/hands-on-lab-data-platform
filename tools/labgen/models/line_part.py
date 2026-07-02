"""Value object representing one source line and its original line ending."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LinePart:
    """Stores split-line details while preserving exact text formatting."""

    original: str
    content: str
    ending: str
