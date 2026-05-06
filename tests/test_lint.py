"""Tests for envault.lint"""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.lint import LintError, LintIssue, lint_env_file


@pytest.fixture()
def env_file(tmp_path: Path):
    """Return a factory that writes content to a temp .env file."""
    p = tmp_path / ".env"

    def _write(content: str) -> Path:
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def test_lint_clean_file(env_file):
    p = env_file("FOO=bar\nBAZ=qux\n")
    issues = lint_env_file(p)
    assert issues == []


def test_lint_missing_file(tmp_path):
    with pytest.raises(LintError, match="not found"):
        lint_env_file(tmp_path / "nonexistent.env")


def test_lint_invalid_key(env_file):
    p = env_file("123INVALID=value\n")
    issues = lint_env_file(p)
    codes = [i.code for i in issues]
    assert "E001" in codes


def test_lint_duplicate_key(env_file):
    p = env_file("FOO=bar\nFOO=baz\n")
    issues = lint_env_file(p)
    codes = [i.code for i in issues]
    assert "E002" in codes


def test_lint_missing_equals(env_file):
    p = env_file("NODEFINITION\n")
    issues = lint_env_file(p)
    codes = [i.code for i in issues]
    assert "E003" in codes


def test_lint_unquoted_whitespace(env_file):
    p = env_file("FOO=hello world\n")
    issues = lint_env_file(p)
    codes = [i.code for i in issues]
    assert "W001" in codes


def test_lint_inline_comment_warning(env_file):
    p = env_file("FOO=bar#comment\n")
    issues = lint_env_file(p)
    codes = [i.code for i in issues]
    assert "W002" in codes


def test_lint_quoted_value_no_warnings(env_file):
    p = env_file('FOO="hello world # not a comment"\n')
    issues = lint_env_file(p)
    assert issues == []


def test_lint_comments_and_blanks_ignored(env_file):
    p = env_file("# This is a comment\n\nFOO=bar\n")
    issues = lint_env_file(p)
    assert issues == []


def test_lint_issue_str():
    issue = LintIssue(line_no=3, code="E001", message="Bad key")
    assert "Line 3" in str(issue)
    assert "E001" in str(issue)
    assert "Bad key" in str(issue)


def test_lint_multiple_issues(env_file):
    content = "123BAD=val\nFOO=bar\nFOO=baz\nNOEQUALS\n"
    p = env_file(content)
    issues = lint_env_file(p)
    codes = {i.code for i in issues}
    assert "E001" in codes
    assert "E002" in codes
    assert "E003" in codes
