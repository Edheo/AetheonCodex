import unittest
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import index


class IndexTests(unittest.TestCase):
    def test_includes_canonical_version(self):
        with patch.object(index, "read_version", return_value="1.2.3"):
            result = index.build()

        self.assertIn("> **Versión publicada:** 1.2.3", result)

    def test_rejects_empty_version(self):
        with tempfile.TemporaryDirectory() as directory:
            version_file = Path(directory) / "VERSION"
            version_file.write_text("\n", encoding="utf-8")
            with patch.object(index, "VERSION_FILE", version_file):
                with self.assertRaisesRegex(ValueError, "VERSION no puede estar vacío"):
                    index.read_version()

    def test_rejects_invalid_version(self):
        with tempfile.TemporaryDirectory() as directory:
            version_file = Path(directory) / "VERSION"
            version_file.write_text("release-next\n", encoding="utf-8")
            with patch.object(index, "VERSION_FILE", version_file):
                with self.assertRaisesRegex(ValueError, "formato X.Y.Z"):
                    index.read_version()


if __name__ == "__main__":
    unittest.main()
