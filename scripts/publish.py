"""
Aetheon Publisher

Publica en GitHub un estado previamente preparado,
commiteado y validado del repositorio.

Este script NO crea commits.
Este script NO modifica contenido.

Flujo:

    Check clean repository
        ↓
    Check branch
        ↓
    Check remote
        ↓
    Final build
        ↓
    Check repository remains clean
        ↓
    Confirmation
        ↓
    Git push
"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
PUBLISH_BRANCH = "main"
REMOTE = "origin"


def run(command):
    """
    Ejecuta un comando y devuelve su resultado.

    Si el comando falla, aborta inmediatamente.
    """

    print(f"\n> {' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, end="")

    if result.returncode != 0:
        print()
        print("[ERROR] Command failed.")
        sys.exit(result.returncode)

    return result


def check_clean_worktree():
    """
    Comprueba que no existen cambios locales sin commit.
    """

    print("\n[PUBLISH] Checking working tree...")

    result = run(
        [
            "git",
            "status",
            "--porcelain",
        ]
    )

    if result.stdout.strip():

        print()
        print("[ERROR] Repository contains uncommitted changes.")
        print("Commit all pending changes before publishing.")

        sys.exit(1)

    print("[OK] Working tree is clean.")


def get_current_branch():
    """
    Devuelve la rama Git actual.
    """

    result = run(
        [
            "git",
            "branch",
            "--show-current",
        ]
    )

    return result.stdout.strip()


def check_branch():
    """
    Comprueba que la publicación se realiza desde main.
    """

    print("\n[PUBLISH] Checking branch...")

    branch = get_current_branch()

    if branch != PUBLISH_BRANCH:

        print()
        print(f"[ERROR] Current branch is '{branch}'.")
        print(
            f"Publishing is only allowed from "
            f"'{PUBLISH_BRANCH}'."
        )

        sys.exit(1)

    print(f"[OK] Branch: {branch}.")


def check_remote_state():
    """
    Actualiza la información del remoto y comprueba
    que la rama local no esté por detrás de origin/main.

    Estar por delante es correcto:
    esos son precisamente los commits que se publicarán.
    """

    print("\n[PUBLISH] Checking remote state...")

    run(
        [
            "git",
            "fetch",
            REMOTE,
        ]
    )

    result = run(
        [
            "git",
            "status",
            "--branch",
            "--porcelain",
        ]
    )

    status = result.stdout

    if "behind" in status:

        print()
        print("[ERROR] Local branch is behind remote.")
        print("Synchronize the repository before publishing.")

        sys.exit(1)

    print("[OK] Remote state is compatible.")


def final_build():
    """
    Ejecuta el Builder completo como validación final.
    """

    print("\n[PUBLISH] Running final build...")

    run(
        [
            sys.executable,
            "scripts/build.py",
        ]
    )

    print("[OK] Final build completed.")


def get_commit():
    """
    Obtiene el commit HEAD que se va a publicar.
    """

    result = run(
        [
            "git",
            "log",
            "-1",
            "--oneline",
        ]
    )

    return result.stdout.strip()


def get_unpublished_commits():
    """
    Obtiene los commits locales todavía no publicados.
    """

    result = run(
        [
            "git",
            "log",
            f"{REMOTE}/{PUBLISH_BRANCH}..HEAD",
            "--oneline",
        ]
    )

    return result.stdout.strip()


def show_summary(commit, unpublished_commits):
    """
    Muestra el resumen final antes de pedir confirmación.
    """

    print()
    print("=" * 50)
    print(" AETHEON PUBLISH")
    print("=" * 50)

    print()
    print("Current commit:")
    print(f"  {commit}")

    print()
    print("Commits to publish:")

    if unpublished_commits:
        print(unpublished_commits)
    else:
        print("  No unpublished commits.")

    print()
    print("Checks:")
    print("  ✓ Working tree clean")
    print(f"  ✓ Branch: {PUBLISH_BRANCH}")
    print("  ✓ Remote state compatible")
    print("  ✓ Final build successful")
    print("  ✓ Working tree still clean")

    print()
    print("-" * 50)


def ask_confirmation():
    """
    Solicita confirmación explícita antes del push.
    """

    answer = input(
        "\nPublish these commits to GitHub? [y/N]: "
    ).strip().lower()

    return answer == "y"


def publish():
    """
    Publica la rama actual en GitHub.
    """

    print("\n[PUBLISH] Pushing to GitHub...")

    run(
        [
            "git",
            "push",
            REMOTE,
            PUBLISH_BRANCH,
        ]
    )


def main():

    print()
    print("=" * 50)
    print(" AETHEON PUBLISH")
    print("=" * 50)

    # El estado inicial debe haber sido preparado
    # deliberadamente por el usuario.
    check_clean_worktree()

    # Sólo publicamos desde main.
    check_branch()

    # Actualizamos la información remota y comprobamos
    # que no estemos detrás de GitHub.
    check_remote_state()

    # El estado commiteado debe poder reconstruirse
    # completamente.
    final_build()

    # Muy importante:
    # si el Builder ha generado cualquier diferencia,
    # el estado publicado ya no coincidiría con el
    # estado commiteado y debemos abortar.
    check_clean_worktree()

    commit = get_commit()
    unpublished_commits = get_unpublished_commits()

    show_summary(
        commit,
        unpublished_commits,
    )

    # Si no hay nada nuevo que publicar,
    # no tiene sentido ejecutar git push.
    if not unpublished_commits:

        print()
        print("[PUBLISH] Nothing to publish.")

        return

    if not ask_confirmation():

        print()
        print("[PUBLISH] Publication cancelled.")

        return

    publish()

    print()
    print("[PUBLISH] Aetheon published successfully.")


if __name__ == "__main__":
    main()