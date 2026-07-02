"""Service that identifies files eligible for Lab marker transformation."""

from pathlib import Path


class TextFileDetector:
    """Determines whether a file should be parsed for Lab marker blocks."""

    def __init__(self, extensions: set[str] | None = None) -> None:
        """Initialize allowed extensions, defaulting to Python files only."""
        if extensions is None:
            extensions = {
                ".py",
            }
        self._extensions = {extension.lower() for extension in extensions}

    def is_text_file(self, path: Path) -> bool:
        """Return True if the file extension is configured for marker parsing."""
        return path.suffix.lower() in self._extensions
