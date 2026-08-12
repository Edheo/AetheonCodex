from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent


def run(command):
    """Ejecuta un comando y devuelve su resultado."""

    print(f"\n> {' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print("\n[ERROR] El comando ha fallado.")
        sys.exit(result.returncode)

    return result


def check_clean_worktree():
    """Comprueba que no existen cambios sin commit."""

    print("\n[PUBLISH] Checking working tree...")

    result = run([
        "git",
        "status",
        "--porcelain",
    ])

    if result.stdout.strip():
        print(
            "\n[ERROR] Repository contains uncommitted changes."
        )
        print(
            "Commit all pending changes before publishing."
        )
        sys.exit(1)

    print("[OK] Working tree is clean.")


def check_branch():
    """Comprueba la rama actual."""

    result = run([
        "git",
        "branch",
        "--show-current",
    ])

    branch = result.stdout.strip()

    if branch != "main":
        print(
            f"\n[ERROR] Current branch is '{branch}'."
        )
        print(
            "Publishing is only allowed from 'main'."
        )
        sys.exit(1)

    print("[OK] Branch: main.")


def check_remote_state():
    """Comprueba si la rama local está sincronizada."""

    print("\n[PUBLISH] Checking remote state...")

    run(["git", "fetch"])

    result = run([
        "git",
        "status",
        "--branch",
        "--porcelain",
    ])

    status = result.stdout

    if "behind" in status:
        print(
            "\n[ERROR] Local branch is behind remote."
        )
        print(
            "Synchronize the repository before publishing."
        )
        sys.exit(1)

    print("[OK] Remote state is compatible.")


def build_codex():
    """Genera el Codex."""

    print("\n[PUBLISH] Building Codex...")

    run([
        sys.executable,
        "scripts/codex.py",
    ])


def build_site():
    """Construye la documentación MkDocs."""

    print("\n[PUBLISH] Building MkDocs site...")

    run([
        "mkdocs",
        "build",
    ])


def get_commit():
    """Obtiene el commit que se va a publicar."""

    result = run([
        "git",
        "log",
        "-1",
        "--oneline",
    ])

    return result.stdout.strip()


def show_summary(commit):
    print("\n")
    print("=" * 50)
    print(" AETHEON PUBLISH")
    print("=" * 50)

    print("\nCommit to publish:")
    print(f"  {commit}")

    print("\nChecks:")
    print("  ✓ Working tree clean")
    print("  ✓ Main branch")
    print("  ✓ Remote synchronized")
    print("  ✓ Codex built")
    print("  ✓ MkDocs built")

    print("\n" + "-" * 50)


def ask_confirmation():
    answer = input(
        "\nPublish this commit to GitHub? [y/N]: "
    ).strip().lower()

    return answer == "y"


def publish():
    print("\n[PUBLISH] Pushing to GitHub...")

    run([
        "git",
        "push",
        "origin",
        "main",
    ])


def main():
    print("\n")
    print("=" * 50)
    print(" AETHEON PUBLISH")
    print("=" * 50)

    check_clean_worktree()
    check_branch()
    check_remote_state()

    build_codex()
    build_site()

    # El build podría haber generado cambios.
    # Volvemos a comprobar que el estado sigue limpio.
    check_clean_worktree()

    commit = get_commit()

    show_summary(commit)

    if not ask_confirmation():
        print("\n[PUBLISH] Publication cancelled.")
        return

    publish()

    print("\n[PUBLISH] Aetheon published successfully.")


if __name__ == "__main__":
    main()