"""Pattern matching utility for include/exclude manifest globs."""

import re


class GlobMatcher:
    """Evaluates path strings against simplified glob patterns."""

    def is_match(self, path: str, pattern: str) -> bool:
        """Return True when a path matches one manifest glob pattern."""
        normalized_path = path.replace("\\", "/")
        normalized_pattern = pattern.replace("\\", "/")
        escaped = re.escape(normalized_pattern)
        escaped = escaped.replace(r"\*\*", "__DOUBLE_WILDCARD__")
        escaped = escaped.replace(r"\*", "[^/]*")
        escaped = escaped.replace("__DOUBLE_WILDCARD__", ".*")
        regex = f"^{escaped}$"
        return re.match(regex, normalized_path, re.IGNORECASE) is not None
