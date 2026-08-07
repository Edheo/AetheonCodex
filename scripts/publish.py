"""
Publica el Atlas mediante MkDocs.

Responsabilidades:

- mkdocs build
- mkdocs serve
"""

import subprocess
import sys

def build():
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build"],
        check=True
    )


def serve():
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "serve"],
        check=True
    )


def run():
    print("[PUBLISH] Building site...")
    build()
    print("[PUBLISH] Done.")