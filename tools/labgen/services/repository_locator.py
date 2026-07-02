"""Service for discovering the Git repository root used by LabGen."""

from pathlib import Path


class RepositoryLocator:
    """Finds the repository root by walking parent directories."""

    def find_root(self, start_path: Path) -> Path:
        """Return the nearest parent directory that contains .git."""
        directory = start_path.resolve()
        for candidate in [directory, *directory.parents]:
            if (candidate / ".git").exists():
                return candidate
        raise RuntimeError(
            "Unable to locate repository root from the current directory."
        )
