"""Service that yields repository files matching manifest include/exclude rules."""

from pathlib import Path
from typing import Iterable

from ..models import LabManifest
from .glob_matcher import GlobMatcher


class IncludedFileEnumerator:
    """Enumerates files that must be copied/transformed into generated labs."""

    def __init__(self, glob_matcher: GlobMatcher) -> None:
        self._glob_matcher = glob_matcher

    def enumerate(self, repository_root: Path, manifest: LabManifest) -> Iterable[Path]:
        """Yield every file that passes include and exclude glob filters."""
        for path in repository_root.rglob("*"):
            if not path.is_file():
                continue

            if self._is_under_directory(path, repository_root / ".git"):
                continue

            if self._is_under_directory(path, repository_root / manifest.output_root):
                continue

            relative_path = path.relative_to(repository_root).as_posix()

            if any(
                self._glob_matcher.is_match(relative_path, pattern)
                for pattern in manifest.exclude
            ):
                continue

            if any(
                self._glob_matcher.is_match(relative_path, pattern)
                for pattern in manifest.include
            ):
                yield path

    def _is_under_directory(self, path: Path, directory: Path) -> bool:
        """Return True when path is located inside directory."""
        try:
            path.resolve().relative_to(directory.resolve())
            return True
        except ValueError:
            return False
