"""Documenta la primera incorporación conservada en Git, siguiendo renombrados.

Sin --apply solo muestra la propuesta. Nunca sustituye fechas ya registradas.
Usa la fecha del committer (con su zona original), no la fecha del suceso ni
la creación del archivo en disco. No inventa fechas para archivos sin historial.
"""
from pathlib import Path
from datetime import datetime
import argparse
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
FIELD = "Primera incorporación al Codex"


def first_incorporation(root, path):
    history = subprocess.check_output(
        ["git", "log", "--follow", "--name-status", "--format=COMMIT %H %cI",
         "--", path.relative_to(root).as_posix()], cwd=root,
    ).decode("utf-8").strip().splitlines()
    evidence = None
    earliest_addition = None
    for line in history:
        if line.startswith("COMMIT "):
            _, commit, timestamp = line.split()
            evidence = datetime.fromisoformat(timestamp).date().isoformat(), commit
        elif re.match(r"^A\t", line):
            earliest_addition = evidence
        elif re.match(r"^C\d+\t", line):
            # --follow can follow copies too. A new entry copied from an old
            # one starts here; only renames retain the original history.
            return earliest_addition or evidence
    return earliest_addition


def annotate(text, evidence):
    if FIELD in text:
        return text
    day, commit = evidence
    newline = "\r\n" if "\r\n" in text else "\n"
    pattern = r"(### Autoría\r?\n.*?)(?=\r?\n### |\r?\n## |\Z)"
    def insert(match):
        return (match[1].rstrip("\r\n") + newline * 2
                + "### " + FIELD + newline + day + newline
                + "<!-- Fuente: Git; commit " + commit
                + "; fecha de incorporación documentada, no de escritura. -->"
                + newline)
    result, count = re.subn(pattern, insert, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("No se encontró un bloque de autoría inequívoco")
    return result


def run(apply=False):
    """Completa únicamente metadatos ausentes; reutilizable desde el build."""
    shallow = subprocess.check_output(
        ["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT,
    ).strip()
    if shallow == b"true":
        raise SystemExit("Historial incompleto: no se asignarán fechas.")
    changes = []
    for path in sorted((ROOT / "codex" / "04_Bitacora").glob("*.md")):
        text = path.read_bytes().decode("utf-8")
        if FIELD in text:
            continue
        evidence = first_incorporation(ROOT, path)
        if evidence is None:
            print(f"Sin historial: {path.name}; se mantiene sin fecha.")
            continue
        updated = annotate(text, evidence)
        changes.append((path, updated))
        print(f"{path.name}: {evidence[0]} ({evidence[1][:8]})")
    if apply:
        for path, text in changes:
            path.write_bytes(text.encode("utf-8"))
    print(f"{len(changes)} entradas {'actualizadas' if apply else 'propuestas'}.")
    return len(changes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    run(apply=args.apply)


if __name__ == "__main__":
    main()
