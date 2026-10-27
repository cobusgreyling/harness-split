import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from harness_split.__main__ import main
from harness_split.classify import (
    BUCKETS,
    classify_path,
    format_headline,
    format_table,
    integer_shares,
    score_dir,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "tiny-harness"

EXPECTED = {
    "prompt.md": "model",
    "model.json": "model",
    "tools/lookup.json": "tools",
    "tools/update.json": "tools",
    "tools/confirm.json": "tools",
    "memory/profile.md": "memory",
    "memory/session.json": "memory",
    "evals/cases.jsonl": "evals",
    "evals/rubric.md": "evals",
    "gates/ship.yaml": "gates",
}


class SplitTests(unittest.TestCase):
    def test_fixture_buckets_and_share(self) -> None:
        report = score_dir(FIXTURE)
        found = {row.path: row.bucket for row in report.files}
        self.assertEqual(found, EXPECTED)
        for row in report.files:
            disk = (FIXTURE / row.path).read_text(encoding="utf-8")
            self.assertEqual(row.lines, len(disk.splitlines()))
            self.assertGreater(row.lines, 0)
        self.assertEqual(report.file_counts["unclassified"], 0)
        self.assertEqual(report.lines["unclassified"], 0)
        shares = integer_shares([report.lines[name] for name in BUCKETS])
        self.assertEqual([report.share[name] for name in BUCKETS], shares)
        self.assertEqual(sum(shares), 100)
        self.assertLess(report.share["model"], 50)
        self.assertGreater(report.lines["tools"], report.lines["model"])
        self.assertIn("Not the model:", format_headline(report))

    def test_readme_quotes_the_demo(self) -> None:
        report = score_dir(FIXTURE)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(format_headline(report), readme)
        self.assertIn(format_table(report), readme)
        self.assertTrue(readme.startswith("![harness-split](assets/header.png)\n"))

    def test_path_beats_stem_and_unknown_is_unclassified(self) -> None:
        self.assertEqual(classify_path(Path("tools/model.json")), "tools")
        self.assertEqual(classify_path(Path("memory/prompt.md")), "memory")
        self.assertEqual(classify_path(Path("prompts/system.md")), "model")
        self.assertEqual(classify_path(Path("policy.yaml")), "gates")
        self.assertEqual(classify_path(Path("notes.txt")), "unclassified")

    def test_hidden_and_cache_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "model.json").write_text('{"name":"small"}\n', encoding="utf-8")
            (root / ".secret").write_text("hidden\n", encoding="utf-8")
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "model.pyc").write_bytes(b"\x00\x01")
            nested = root / "tools"
            nested.mkdir()
            (nested / "lookup.json").write_text("{}\n", encoding="utf-8")
            report = score_dir(root)
            self.assertEqual([row.path for row in report.files], ["model.json", "tools/lookup.json"])
            self.assertEqual(report.share["model"], 50)
            self.assertEqual(report.share["tools"], 50)

    def test_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = score_dir(Path(directory))
            self.assertEqual(report.files, ())
            self.assertEqual(report.classified_lines, 0)
            self.assertEqual(format_headline(report), "Harness split: no classified lines.")
            self.assertEqual(sum(report.share.values()), 0)

    def test_integer_shares_exact_and_ties(self) -> None:
        self.assertEqual(integer_shares([0, 0, 0, 0, 0]), [0, 0, 0, 0, 0])
        self.assertEqual(integer_shares([1, 1, 1, 1, 1]), [20, 20, 20, 20, 20])
        self.assertEqual(integer_shares([3, 0, 0, 0, 0]), [100, 0, 0, 0, 0])

    def test_cli_prints_table_and_rejects_a_file(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main([str(FIXTURE), "--verbose"])
        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("prompt.md", text)
        self.assertIn("bucket", text)
        self.assertIn("unclassified", text)

        stderr = StringIO()
        with redirect_stderr(stderr):
            code = main([str(FIXTURE / "prompt.md")])
        self.assertEqual(code, 2)
        self.assertIn("not a directory", stderr.getvalue())

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["--help"]), 0)
        self.assertIn("usage:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
