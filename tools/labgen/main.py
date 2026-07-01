from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


STARTER = "starter"
SOLUTION = "solution"


@dataclass(frozen=True)
class LabDefinition:
    id: str
    markdown: str


@dataclass(frozen=True)
class LabManifest:
    output_root: str = "generated/labs"
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    labs: list[LabDefinition] = field(default_factory=list)


@dataclass(frozen=True)
class LinePart:
    original: str
    content: str
    ending: str


class LabMarkerProcessor:
    """Transforms lab markers into starter or solution payload."""

    _start_marker = re.compile(r'^\s*#\s*<lab\s+id="(?P<id>[^"]+)"(?:\s+state="starter")?\s*>', re.IGNORECASE)
    _end_marker = re.compile(r"^\s*#\s*</lab>\s*$", re.IGNORECASE)
    _hidden_payload = re.compile(r"^(?P<indent>\s*)#\|\s*(?P<content>.*)$")

    @classmethod
    def transform(cls, source: str, target_lab_id: str, target_variant: str, lab_order: dict[str, int]) -> str:
        target_lab_index = lab_order[target_lab_id]
        lines = cls._split_lines(source)
        output: list[str] = []

        cls._transform_range(lines, 0, len(lines), output, target_lab_index, target_variant, lab_order)

        return "".join(output)

    @classmethod
    def _transform_range(
        cls,
        lines: list[LinePart],
        start_index: int,
        end_index: int,
        output: list[str],
        target_lab_index: int,
        target_variant: str,
        lab_order: dict[str, int],
    ) -> None:
        index = start_index
        while index < end_index:
            line = lines[index]
            marker = cls._start_marker.match(line.content)
            if marker is None:
                if not cls._hidden_payload.match(line.content):
                    output.append(line.original)
                index += 1
                continue

            block_lab_id = marker.group("id")
            selected_state = cls._resolve_state(block_lab_id, target_lab_index, target_variant, lab_order)
            block_end_index = cls._find_block_end(lines, index + 1, end_index, block_lab_id)

            if selected_state == STARTER:
                cls._add_starter_payload(lines, index + 1, block_end_index, output)
            else:
                cls._transform_range(lines, index + 1, block_end_index, output, target_lab_index, target_variant, lab_order)

            index = block_end_index + 1

    @classmethod
    def _add_starter_payload(cls, lines: list[LinePart], start_index: int, end_index: int, output: list[str]) -> None:
        index = start_index
        while index < end_index:
            if cls._start_marker.match(lines[index].content):
                index = cls._find_block_end(lines, index + 1, end_index, "nested") + 1
                continue

            if cls._hidden_payload.match(lines[index].content):
                output.append(cls._unwrap_lab_line(lines[index]))
            index += 1

    @classmethod
    def _find_block_end(cls, lines: list[LinePart], start_index: int, end_index: int, block_lab_id: str) -> int:
        depth = 0
        for index in range(start_index, end_index):
            if cls._start_marker.match(lines[index].content):
                depth += 1
                continue

            if not cls._end_marker.match(lines[index].content):
                continue

            if depth == 0:
                return index

            depth -= 1

        raise ValueError(f"Missing closing lab marker for lab '{block_lab_id}'.")

    @staticmethod
    def _resolve_state(block_lab_id: str, target_lab_index: int, target_variant: str, lab_order: dict[str, int]) -> str:
        block_lab_index = lab_order.get(block_lab_id)
        if block_lab_index is None:
            return STARTER

        if block_lab_index == target_lab_index:
            return target_variant

        return SOLUTION if block_lab_index < target_lab_index else STARTER

    @classmethod
    def _unwrap_lab_line(cls, line: LinePart) -> str:
        match = cls._hidden_payload.match(line.content)
        if match is None:
            return line.original
        return f"{match.group('indent')}{match.group('content')}{line.ending}"

    @staticmethod
    def _split_lines(source: str) -> list[LinePart]:
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
            lines.append(LinePart(original=source[start : newline_index + 1], content=line_content, ending=ending))
            start = newline_index + 1

        return lines


def find_repository_root(start_path: Path) -> Path:
    directory = start_path.resolve()
    for candidate in [directory, *directory.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("Unable to locate repository root from the current directory.")


def load_manifest(manifest_path: Path) -> LabManifest:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    labs = [
        LabDefinition(
            id=str(item["id"]),
            markdown=str(item.get("markdown", "")),
        )
        for item in data.get("labs", [])
    ]
    return LabManifest(
        output_root=str(data.get("outputRoot", "generated/labs")),
        include=[str(item) for item in data.get("include", [])],
        exclude=[str(item) for item in data.get("exclude", [])],
        labs=labs,
    )


def list_labs(manifest: LabManifest) -> int:
    for lab in manifest.labs:
        print(f"{lab.id}: {lab.markdown}")
    return 0


def generate_labs(repository_root: Path, manifest: LabManifest, requested_lab_id: str | None) -> int:
    labs = manifest.labs if requested_lab_id is None else [lab for lab in manifest.labs if lab.id == requested_lab_id]
    if not labs:
        print(f"Unknown lab: {requested_lab_id}", file=sys.stderr)
        return 1

    if requested_lab_id is None:
        output_root = repository_root / manifest.output_root
        if output_root.exists():
            shutil.rmtree(output_root)

    for lab in labs:
        generate_lab(repository_root, manifest, lab)

    return 0


def generate_lab(repository_root: Path, manifest: LabManifest, lab: LabDefinition) -> None:
    output_root = repository_root / manifest.output_root / lab.id
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    files = list(enumerate_included_files(repository_root, manifest))
    lab_order = {entry.id: index for index, entry in enumerate(manifest.labs)}

    for source_path in files:
        relative_path = source_path.relative_to(repository_root)
        destination_path = output_root / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        if is_text_file(source_path):
            source = source_path.read_text(encoding="utf-8")
            transformed = LabMarkerProcessor.transform(source, lab.id, STARTER, lab_order)
            destination_path.write_text(transformed, encoding="utf-8")
        else:
            shutil.copy2(source_path, destination_path)

    print(f"Generated {output_root.relative_to(repository_root)}")


def enumerate_included_files(repository_root: Path, manifest: LabManifest) -> Iterable[Path]:
    for path in repository_root.rglob("*"):
        if not path.is_file():
            continue

        if is_under_directory(path, repository_root / ".git"):
            continue

        if is_under_directory(path, repository_root / manifest.output_root):
            continue

        relative_path = path.relative_to(repository_root).as_posix()

        if any(glob_match(relative_path, pattern) for pattern in manifest.exclude):
            continue

        if any(glob_match(relative_path, pattern) for pattern in manifest.include):
            yield path


def is_under_directory(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in {
        ".py",
        ".json",
        ".md",
        ".http",
        ".yaml",
        ".yml",
        ".tf",
        ".xml",
        ".toml",
        ".txt",
        ".lock",
        ".sh",
    }


def glob_match(path: str, pattern: str) -> bool:
    normalized_path = path.replace("\\", "/")
    normalized_pattern = pattern.replace("\\", "/")
    escaped = re.escape(normalized_pattern)
    escaped = escaped.replace(r"\*\*", "__DOUBLE_WILDCARD__")
    escaped = escaped.replace(r"\*", "[^/]*")
    escaped = escaped.replace("__DOUBLE_WILDCARD__", ".*")
    regex = f"^{escaped}$"
    return re.match(regex, normalized_path, re.IGNORECASE) is not None


def unknown_command(command: str) -> int:
    print(f"Unknown command: {command}", file=sys.stderr)
    print("Usage:", file=sys.stderr)
    print("  python -m tools.labgen list", file=sys.stderr)
    print("  python -m tools.labgen generate [--lab <id>]", file=sys.stderr)
    return 1


def read_option(args: list[str], name: str) -> str | None:
    for index, arg in enumerate(args):
        if arg == name and index + 1 < len(args):
            return args[index + 1]
    return None


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    repository_root = find_repository_root(Path.cwd())
    manifest_path = repository_root / "docs" / "manifest.json"

    if not manifest_path.exists():
        print(f"Missing manifest: {manifest_path.relative_to(repository_root)}", file=sys.stderr)
        return 1

    manifest = load_manifest(manifest_path)

    command = args[0] if args else "generate"

    if command == "list":
        return list_labs(manifest)

    if command == "generate":
        command_args = args[1:]
        if read_option(command_args, "--variant") is not None:
            print("--variant is no longer supported. LabGen now generates one starter snapshot per lab.", file=sys.stderr)
            return 1
        return generate_labs(repository_root, manifest, read_option(command_args, "--lab"))

    return unknown_command(command)


if __name__ == "__main__":
    raise SystemExit(main())
