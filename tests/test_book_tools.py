import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "book_tools.py"
)
SPEC = importlib.util.spec_from_file_location(
    "book_tools",
    MODULE_PATH,
)
book_tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(book_tools)


class GitWarningTests(unittest.TestCase):
    def test_unrelated_changes_keep_standard_confirmation(self):
        target = (book_tools.ROOT / "codex" / "target.md").resolve()
        unrelated = (book_tools.ROOT / "README.md").resolve()

        with patch.object(
            book_tools,
            "get_changed_git_paths",
            return_value={unrelated},
        ), patch("builtins.input", return_value="y") as prompt:
            self.assertTrue(book_tools.confirm_changes([target]))

        self.assertIn("[y/N]", prompt.call_args.args[0])

    def test_modified_target_requires_exact_apply_confirmation(self):
        target = (book_tools.ROOT / "codex" / "target.md").resolve()

        with patch.object(
            book_tools,
            "get_changed_git_paths",
            return_value={target},
        ), patch("builtins.input", return_value="y"):
            self.assertFalse(book_tools.confirm_changes([target]))

        with patch.object(
            book_tools,
            "get_changed_git_paths",
            return_value={target},
        ), patch("builtins.input", return_value="APPLY"):
            self.assertTrue(book_tools.confirm_changes([target]))


class SourceSnapshotTests(unittest.TestCase):
    def test_changed_source_aborts_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.md"
            second = root / "second.md"
            first.write_text("changed", encoding="utf-8")
            second.write_text("original", encoding="utf-8")
            prepared = [
                (first, "renumbered first"),
                (second, "renumbered second"),
            ]
            originals = {
                first: "original",
                second: "original",
            }

            with self.assertRaises(SystemExit):
                book_tools.write_prepared_changes(prepared, originals)

            self.assertEqual(
                first.read_text(encoding="utf-8"),
                "changed",
            )
            self.assertEqual(
                second.read_text(encoding="utf-8"),
                "original",
            )


class ChapterPlanTests(unittest.TestCase):
    @staticmethod
    def entry(number, title):
        return {
            "chapter_number": number,
            "chapter_title": title,
            "path": Path(f"chapter-{number}.md"),
        }

    def test_first_regular_chapter_starts_at_step(self):
        entries = [
            self.entry(1, "Uno"),
            self.entry(2, "Dos"),
            self.entry(3, "Tres"),
        ]

        plan = book_tools.build_chapter_plan(entries, step=10)

        self.assertEqual(
            [item["new"] for item in plan],
            [10, 20, 30],
        )

    def test_zero_is_preserved_and_regular_chapters_start_at_step(self):
        entries = [
            self.entry(0, "Prólogo"),
            self.entry(1, "Uno"),
            self.entry(2, "Dos"),
        ]

        plan = book_tools.build_chapter_plan(entries, step=10)

        self.assertEqual(
            [item["new"] for item in plan],
            [0, 10, 20],
        )

    def test_default_step_keeps_consecutive_numbering(self):
        entries = [
            self.entry(4, "Uno"),
            self.entry(8, "Dos"),
        ]

        plan = book_tools.build_chapter_plan(entries, step=1)

        self.assertEqual(
            [item["new"] for item in plan],
            [1, 2],
        )


class GitPathTests(unittest.TestCase):
    def test_collects_worktree_index_and_untracked_paths(self):
        results = [
            subprocess.CompletedProcess([], 0, b"one.md\0", b""),
            subprocess.CompletedProcess([], 0, b"two.md\0", b""),
            subprocess.CompletedProcess([], 0, b"three.md\0", b""),
        ]

        with patch.object(
            book_tools.subprocess,
            "run",
            side_effect=results,
        ):
            changed = book_tools.get_changed_git_paths()

        self.assertEqual(
            changed,
            {
                (book_tools.ROOT / "one.md").resolve(),
                (book_tools.ROOT / "two.md").resolve(),
                (book_tools.ROOT / "three.md").resolve(),
            },
        )


if __name__ == "__main__":
    unittest.main()
