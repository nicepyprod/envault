"""Tests for envault.sync (git sync utilities)."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from envault.sync import SyncError, is_git_repo, pull, push


# ---------------------------------------------------------------------------
# is_git_repo
# ---------------------------------------------------------------------------

def _make_completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    cp = MagicMock(spec=subprocess.CompletedProcess)
    cp.returncode = returncode
    cp.stderr = stderr
    cp.stdout = ""
    return cp


@patch("envault.sync.subprocess.run")
def test_is_git_repo_true(mock_run):
    mock_run.return_value = _make_completed(0)
    assert is_git_repo(Path("/some/repo")) is True


@patch("envault.sync.subprocess.run")
def test_is_git_repo_false(mock_run):
    mock_run.return_value = _make_completed(1)
    assert is_git_repo(Path("/not/a/repo")) is False


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

@patch("envault.sync._run")
@patch("envault.sync.subprocess.run")
def test_push_commits_and_pushes_when_staged(mock_run, mock__run):
    # git rev-parse succeeds (is a repo), git diff --cached returns 1 (changes)
    mock_run.side_effect = [
        _make_completed(0),   # is_git_repo -> rev-parse
        _make_completed(1),   # diff --cached -> changes present
    ]
    vault_file = Path("/repo/vault.env.enc")
    push(vault_file)

    assert mock__run.call_count == 3  # add, commit, push


@patch("envault.sync._run")
@patch("envault.sync.subprocess.run")
def test_push_skips_commit_when_nothing_staged(mock_run, mock__run):
    mock_run.side_effect = [
        _make_completed(0),  # is_git_repo
        _make_completed(0),  # diff --cached -> nothing staged
    ]
    vault_file = Path("/repo/vault.env.enc")
    push(vault_file)

    assert mock__run.call_count == 2  # add, push (no commit)


@patch("envault.sync.subprocess.run")
def test_push_raises_when_not_a_repo(mock_run):
    mock_run.return_value = _make_completed(1)  # rev-parse fails
    with pytest.raises(SyncError, match="not inside a git repository"):
        push(Path("/not/a/repo/vault.env.enc"))


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------

@patch("envault.sync._run")
@patch("envault.sync.subprocess.run")
def test_pull_calls_git_pull_rebase(mock_run, mock__run):
    mock_run.return_value = _make_completed(0)  # is_git_repo
    pull(Path("/repo"))
    mock__run.assert_called_once_with(["git", "pull", "--rebase"], cwd=Path("/repo"))


@patch("envault.sync.subprocess.run")
def test_pull_raises_when_not_a_repo(mock_run):
    mock_run.return_value = _make_completed(1)
    with pytest.raises(SyncError, match="not inside a git repository"):
        pull(Path("/not/a/repo"))


# ---------------------------------------------------------------------------
# _run helper
# ---------------------------------------------------------------------------

@patch("envault.sync.subprocess.run")
def test_run_raises_sync_error_on_nonzero(mock_run):
    from envault.sync import _run
    mock_run.return_value = _make_completed(1, stderr="fatal: not a repo")
    with pytest.raises(SyncError, match="fatal: not a repo"):
        _run(["git", "push"], cwd=Path("/tmp"))
