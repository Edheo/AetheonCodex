"""
Aetheon Publisher

Publica en GitHub un estado previamente preparado,
commiteado y validado del repositorio.

Este script NO crea commits.
Este script NO modifica contenido.

Flujo:

    Check clean repository
        ↓
    Check active branch
        ↓
    Fetch remote
        ↓
    Check remote state
        ↓
    Final build
        ↓
    Check repository remains clean
        ↓
    Show summary
        ↓
    Confirmation
        ↓
    Git push
"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
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

    Si Git está en detached HEAD, aborta.
    """

    result = run(
        [
            "git",
            "branch",
            "--show-current",
        ]
    )

    branch = result.stdout.strip()

    if not branch:
        print()
        print("[ERROR] Detached HEAD detected.")
        print("Publishing requires an active Git branch.")
        sys.exit(1)

    return branch


def check_branch():
    """
    Comprueba que existe una rama activa.
    """

    print("\n[PUBLISH] Checking branch...")

    branch = get_current_branch()

    print(f"[OK] Branch: {branch}.")

    return branch


def remote_branch_exists(branch):
    """
    Comprueba si la rama actual ya existe en el remoto.
    """

    result = subprocess.run(
        [
            "git",
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/remotes/{REMOTE}/{branch}",
        ],
        cwd=ROOT,
    )

    return result.returncode == 0


def check_remote_state(branch):
    """
    Actualiza la información del remoto.

    Si la rama existe en remoto, comprueba que
    la rama local no esté por detrás.

    Estar por delante es correcto:
    esos son los commits que queremos publicar.

    Si la rama todavía no existe en remoto,
    también es un estado válido.
    """

    print("\n[PUBLISH] Checking remote state...")

    run(
        [
            "git",
            "fetch",
            REMOTE,
        ]
    )

    if not remote_branch_exists(branch):
        print(
            f"[OK] Remote branch '{REMOTE}/{branch}' "
            "does not exist yet."
        )
        print("[OK] It will be created when publishing.")
        return

    result = run(
        [
            "git",
            "rev-list",
            "--left-right",
            "--count",
            f"{REMOTE}/{branch}...HEAD",
        ]
    )

    counts = result.stdout.strip().split()

    if len(counts) != 2:
        print()
        print("[ERROR] Unable to determine remote state.")
        sys.exit(1)

    behind = int(counts[0])
    ahead = int(counts[1])

    if behind > 0:
        print()
        print(
            f"[ERROR] Local branch is behind "
            f"'{REMOTE}/{branch}' by {behind} commit(s)."
        )
        print("Synchronize the repository before publishing.")
        sys.exit(1)

    print(
        f"[OK] Remote state compatible "
        f"({ahead} commit(s) ahead)."
    )


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
    Obtiene el commit HEAD actual.
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


def get_unpublished_commits(branch):
    """
    Obtiene los commits locales todavía no publicados.

    Si la rama aún no existe en remoto,
    devuelve todos los commits alcanzables desde HEAD.
    """

    if not remote_branch_exists(branch):
        result = run(
            [
                "git",
                "log",
                "--oneline",
                "--decorate",
                "-10",
            ]
        )

        return result.stdout.strip()

    result = run(
        [
            "git",
            "log",
            f"{REMOTE}/{branch}..HEAD",
            "--oneline",
        ]
    )

    return result.stdout.strip()


def show_summary(
    branch,
    commit,
    unpublished_commits,
):
    """
    Muestra el resumen final antes de pedir confirmación.
    """

    print()
    print("=" * 50)
    print(" AETHEON PUBLISH")
    print("=" * 50)

    print()
    print(f"Remote: {REMOTE}")
    print(f"Branch: {branch}")

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
    print(f"  ✓ Active branch: {branch}")
    print("  ✓ Remote state compatible")
    print("  ✓ Final build successful")
    print("  ✓ Working tree still clean")

    print()
    print("-" * 50)


def ask_confirmation(branch):
    """
    Solicita confirmación explícita antes del push.
    """

    answer = input(
        f"\nPublish branch '{branch}' "
        f"to '{REMOTE}'? [y/N]: "
    ).strip().lower()

    return answer == "y"


def publish(branch):
    """
    Publica la rama actual en GitHub.

    -u establece además el upstream, útil especialmente
    para ramas nuevas como feature/*, release/* o hotfix/*.
    """

    print(
        f"\n[PUBLISH] Pushing branch "
        f"'{branch}' to GitHub..."
    )

    run(
        [
            "git",
            "push",
            "-u",
            REMOTE,
            branch,
        ]
    )


def main():
    print()
    print("=" * 50)
    print(" AETHEON PUBLISH")
    print("=" * 50)

    # El repositorio debe estar completamente commiteado.
    check_clean_worktree()

    # Se permite cualquier rama activa.
    branch = check_branch()

    # Comprobamos su relación con el remoto.
    check_remote_state(branch)

    # Ejecutamos el build completo como prueba final.
    final_build()

    # El build no debe generar diferencias respecto
    # al estado que ya estaba commiteado.
    check_clean_worktree()

    commit = get_commit()

    unpublished_commits = get_unpublished_commits(
        branch
    )

    show_summary(
        branch,
        commit,
        unpublished_commits,
    )

    if not unpublished_commits:
        print()
        print("[PUBLISH] Nothing to publish.")
        return

    if not ask_confirmation(branch):
        print()
        print("[PUBLISH] Publication cancelled.")
        return

    publish(branch)

    print()
    print(
        f"[PUBLISH] Branch '{branch}' "
        "published successfully."
    )


if __name__ == "__main__":
    main()