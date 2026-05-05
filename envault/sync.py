"""Git-based sync utilities for envault vault files."""

import subprocess
import os
from pathlib import Path


class SyncError(Exception):
    """Raised when a git sync operation fails."""


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a shell command, raising SyncError on failure."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SyncError(
            f"Command {' '.join(cmd)} failed:\n{result.stderr.strip()}"
        )
    return result


def is_git_repo(path: Path) -> bool:
    """Return True if *path* is inside a git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def push(vault_file: Path, message: str = "chore: update encrypted vault") -> None:
    """Stage *vault_file*, commit, and push to the current remote."""
    repo_root = vault_file.parent
    if not is_git_repo(repo_root):
        raise SyncError(f"{repo_root} is not inside a git repository.")

    _run(["git", "add", str(vault_file.name)], cwd=repo_root)

    # Only commit if there is something staged.
    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_root,
        capture_output=True,
    )
    if diff.returncode != 0:  # changes are staged
        _run(["git", "commit", "-m", message], cwd=repo_root)

    _run(["git", "push"], cwd=repo_root)


def pull(repo_root: Path) -> None:
    """Pull latest changes from the remote into *repo_root*."""
    if not is_git_repo(repo_root):
        raise SyncError(f"{repo_root} is not inside a git repository.")
    _run(["git", "pull", "--rebase"], cwd=repo_root)
