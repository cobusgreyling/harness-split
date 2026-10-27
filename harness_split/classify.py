"""Path rules for the harness split. No model call."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

BUCKETS = ("model", "tools", "memory", "evals", "gates")

# Directory names. The first matching part from the left wins.
PATH_PARTS = {
    "model": "model",
    "models": "model",
    "prompt": "model",
    "prompts": "model",
    "tool": "tools",
    "tools": "tools",
    "memory": "memory",
    "memories": "memory",
    "eval": "evals",
    "evals": "evals",
    "gate": "gates",
    "gates": "gates",
}

# Filename stem, used only when no directory matches.
STEMS = {
    "model": "model",
    "prompt": "model",
    "system": "model",
    "tool": "tools",
    "tools": "tools",
    "memory": "memory",
    "eval": "evals",
    "evals": "evals",
    "gate": "gates",
    "policy": "gates",
}


@dataclass(frozen=True)
class FileRow:
    path: str
    bucket: str
    lines: int


@dataclass(frozen=True)
class Report:
    files: tuple[FileRow, ...]
    file_counts: dict[str, int]
    lines: dict[str, int]
    share: dict[str, int]
    classified_lines: int


def integer_shares(counts: list[int]) -> list[int]:
    """Largest remainder. Ties go to the earlier bucket."""
    total = sum(counts)
    if total <= 0:
        return [0] * len(counts)
    floors = [(100 * count) // total for count in counts]
    leftover = 100 - sum(floors)
    order = sorted(
        range(len(counts)),
        key=lambda i: ((100 * counts[i]) % total, counts[i], -i),
        reverse=True,
    )
    for index in order[:leftover]:
        floors[index] += 1
    return floors


def classify_path(relative: Path) -> str:
    parts = [part.casefold() for part in relative.parts[:-1]]
    for part in parts:
        bucket = PATH_PARTS.get(part)
        if bucket:
            return bucket
    return STEMS.get(relative.stem.casefold(), "unclassified")


def score_dir(root: Path) -> Report:
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    rows: list[FileRow] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if "__pycache__" in relative.parts:
            continue
        rows.append(FileRow(relative.as_posix(), classify_path(relative), _lines(path)))
    return _report(tuple(rows))


def format_headline(report: Report) -> str:
    if report.classified_lines == 0:
        return "Harness split: no classified lines."
    parts = " · ".join(f"{name} {report.share[name]}%" for name in BUCKETS)
    outside = sum(report.share[name] for name in BUCKETS if name != "model")
    return (
        f"Harness split: {parts}\n"
        f"Not the model: {outside}% of classified lines sit in tools, memory, evals, or gates."
    )


def format_table(report: Report) -> str:
    rows = [("bucket", "files", "lines", "share")]
    for name in BUCKETS:
        rows.append((name, str(report.file_counts[name]), str(report.lines[name]), f"{report.share[name]}%"))
    rows.append(
        (
            "unclassified",
            str(report.file_counts["unclassified"]),
            str(report.lines["unclassified"]),
            "--",
        )
    )
    return _align(rows)


def format_details(report: Report) -> str:
    rows = [("path", "bucket", "lines")]
    for row in report.files:
        rows.append((row.path, row.bucket, str(row.lines)))
    if len(rows) == 1:
        rows.append(("(none)", "--", "0"))
    return _align(rows)


def _report(files: tuple[FileRow, ...]) -> Report:
    names = (*BUCKETS, "unclassified")
    file_counts = {name: 0 for name in names}
    lines = {name: 0 for name in names}
    for row in files:
        file_counts[row.bucket] += 1
        lines[row.bucket] += row.lines
    shares = integer_shares([lines[name] for name in BUCKETS])
    return Report(
        files=files,
        file_counts=file_counts,
        lines=lines,
        share={name: share for name, share in zip(BUCKETS, shares)},
        classified_lines=sum(lines[name] for name in BUCKETS),
    )


def _lines(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0
    return len(text.splitlines())


def _align(rows: list[tuple[str, ...]]) -> str:
    widths = [max(len(cell) for cell in column) for column in zip(*rows)]
    lines = []
    for index, row in enumerate(rows):
        lines.append("  ".join(cell.ljust(widths[col]) for col, cell in enumerate(row)).rstrip())
        if index == 0:
            lines.append("  ".join("-" * widths[col] for col in range(len(widths))))
    return "\n".join(lines)
