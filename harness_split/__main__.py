"""CLI: python -m harness_split fixtures/tiny-harness"""

from __future__ import annotations

import sys
from pathlib import Path

from harness_split.classify import format_details, format_headline, format_table, score_dir

_FLAGS = {"--verbose", "--help", "-h"}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    unknown = [arg for arg in args if arg.startswith("-") and arg not in _FLAGS]
    if unknown:
        print(f"unknown flag: {unknown[0]}", file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return 2
    if "--help" in args or "-h" in args:
        print(_usage())
        return 0
    paths = [arg for arg in args if arg not in _FLAGS]
    if len(paths) != 1:
        print(_usage(), file=sys.stderr)
        return 2
    try:
        report = score_dir(Path(paths[0]))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(format_headline(report))
    print()
    print(format_table(report))
    if "--verbose" in args:
        print()
        print(format_details(report))
    return 0


def _usage() -> str:
    return "usage: python -m harness_split [--verbose] <harness-dir>"


if __name__ == "__main__":
    raise SystemExit(main())
