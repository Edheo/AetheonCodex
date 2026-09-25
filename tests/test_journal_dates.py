import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("journal_dates", ROOT / "scripts/journal_dates.py")
dates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dates)
spec = importlib.util.spec_from_file_location("book", ROOT / "scripts/book.py")
book = importlib.util.module_from_spec(spec)
spec.loader.exec_module(book)


class JournalDatesTests(unittest.TestCase):
    def test_build_fills_dates_before_sync_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            journals = root / "codex/04_Bitacora"
            journals.mkdir(parents=True)
            entry = journals / "entry.md"
            original = "## Literaria\n### Autoría\nEdheo\n\n### Contenido\nTexto.\n"
            entry.write_text(original, encoding="utf-8")
            def git(*args):
                return subprocess.check_output(
                    ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args],
                    cwd=root, stderr=subprocess.STDOUT)
            git("init")
            git("add", ".")
            git("commit", "-m", "First entry")
            new_entry = journals / "new.md"
            new_entry.write_text(original, encoding="utf-8")
            with patch.dict(sys.modules, {"journal_dates": dates}), patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
                import build
            def check_sync():
                self.assertIn(dates.FIELD, entry.read_text(encoding="utf-8"))
                self.assertEqual(new_entry.read_text(encoding="utf-8"), original)
            with patch.object(dates, "ROOT", root), patch.object(build.sync, "run", side_effect=check_sync), \
                 patch.object(build.validate, "run"), patch.object(build.index, "run"), \
                 patch.object(build.cartography, "run"), patch.object(build.book, "run"), \
                 patch.object(build.member_journal, "run"), patch.object(build.media, "run"), \
                 patch.object(build, "build_site"):
                build.main()
                first = entry.read_bytes()
                build.main()
                self.assertEqual(entry.read_bytes(), first)
                git("add", ".")
                git("commit", "-m", "Add second entry")
                second_commit = git("rev-parse", "HEAD").decode().strip()
                with patch.object(build.sync, "run"):
                    build.main()
                self.assertIn(dates.FIELD, new_entry.read_text(encoding="utf-8"))
                self.assertIn(second_commit, new_entry.read_text(encoding="utf-8"))

    def test_rename_and_edit_preserve_original_incorporation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args, day=None):
                env = os.environ.copy()
                if day:
                    env.update(GIT_AUTHOR_DATE=day, GIT_COMMITTER_DATE=day)
                return subprocess.check_output(
                    ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     *args], cwd=root, env=env, stderr=subprocess.STDOUT)
            git("init")
            original = root / "original.md"
            original.write_text("Narración conservada.\n" * 20, encoding="utf-8")
            git("add", ".")
            git("commit", "-m", "First", day="2026-08-04T23:30:00-03:00")
            commit = git("rev-parse", "HEAD").decode().strip()
            git("mv", "original.md", "renamed.md")
            git("commit", "-m", "Rename", day="2026-09-24T12:00:00+02:00")
            renamed = root / "renamed.md"
            renamed.write_text(renamed.read_text(encoding="utf-8") + "Revisión.\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-m", "Edit", day="2026-09-25T12:00:00+02:00")
            self.assertEqual(dates.first_incorporation(root, renamed), ("2026-08-04", commit))
            self.assertIsNone(dates.first_incorporation(root, root / "untracked.md"))

    def test_annotation_is_idempotent_and_preserves_content(self):
        text = "## Literaria\r\n### Autoría\r\nEdheo\r\n\r\n### Contenido\r\nMi voz...\r\n"
        updated = dates.annotate(text, ("2026-09-25", "a" * 40))
        self.assertEqual(dates.annotate(updated, ("2027-01-01", "b" * 40)), updated)
        self.assertEqual(book.extract_content(text), book.extract_content(updated))
        # The builder reads files through read_text, which normalizes CRLF.
        self.assertEqual(book.extract_field(updated.replace("\r\n", "\n"), dates.FIELD), "2026-09-25")

    def test_shared_header_displays_date_beside_author(self):
        entry = dict(title="Título", date=None, author="Edheo", music_work=None,
                     music_performer=None, incorporated="2026-09-25")
        header = "\n".join(book.entry_literary_header(entry))
        self.assertIn("Primera incorporación al Codex: 2026-09-25", header)
        self.assertLess(header.index("Autoría"), header.index("Primera incorporación"))
