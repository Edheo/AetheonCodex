import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate


class PrivateMemoryTests(unittest.TestCase):
    def make_root(self, ignore="/private/\n"):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / ".gitignore").write_text(ignore, encoding="utf-8")
        return temporary, root

    def test_accepts_ignored_untracked_private_memory(self):
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)

        result = subprocess.CompletedProcess(
            args=["git"],
            returncode=0,
            stdout="",
            stderr="",
        )

        with (
            patch.object(validate, "ROOT", root),
            patch.object(validate, "GITIGNORE", root / ".gitignore"),
            patch("validate.subprocess.run", return_value=result),
        ):
            validate.validate_private_memory()

    def test_rejects_missing_private_ignore_rule(self):
        temporary, root = self.make_root(ignore="site/\n")
        self.addCleanup(temporary.cleanup)

        with (
            patch.object(validate, "ROOT", root),
            patch.object(validate, "GITIGNORE", root / ".gitignore"),
        ):
            with self.assertRaisesRegex(ValueError, "excluida"):
                validate.validate_private_memory()

    def test_rejects_tracked_private_files(self):
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)

        result = subprocess.CompletedProcess(
            args=["git"],
            returncode=0,
            stdout="private/08_Memoria/LOGOS.md\n",
            stderr="",
        )

        with (
            patch.object(validate, "ROOT", root),
            patch.object(validate, "GITIGNORE", root / ".gitignore"),
            patch("validate.subprocess.run", return_value=result),
        ):
            with self.assertRaisesRegex(ValueError, "rastreando"):
                validate.validate_private_memory()


if __name__ == "__main__":
    unittest.main()
