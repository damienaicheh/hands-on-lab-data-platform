"""Application entry point and dependency composition for LabGen."""

from .cli import LabGenApplication
from .services.file_enumerator import IncludedFileEnumerator
from .services.glob_matcher import GlobMatcher
from .services.lab_generator import LabGenerator
from .services.manifest_loader import ManifestLoader
from .services.marker_processor import LabMarkerProcessor
from .services.repository_locator import RepositoryLocator
from .services.text_file_detector import TextFileDetector
from .structured_logging import configure_structured_logger


def main(argv: list[str] | None = None) -> int:
    """Build runtime services and execute the LabGen command flow."""
    logger = configure_structured_logger()
    glob_matcher = GlobMatcher()
    marker_processor = LabMarkerProcessor()
    file_enumerator = IncludedFileEnumerator(glob_matcher)
    text_file_detector = TextFileDetector()
    lab_generator = LabGenerator(
        marker_processor, file_enumerator, text_file_detector, logger
    )
    repository_locator = RepositoryLocator()
    manifest_loader = ManifestLoader()
    app = LabGenApplication(repository_locator, manifest_loader, lab_generator, logger)

    return app.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
