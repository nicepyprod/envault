"""Lint/validate .env files for common issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class LintError(Exception):
    """Raised when the env file cannot be read or parsed."""


@dataclass
class LintIssue:
    line_no: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line_no}: [{self.code}] {self.message}"


_VALID_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def lint_env_file(env_path: Path) -> List[LintIssue]:
    """Return a list of LintIssue found in *env_path*.

    Checks performed:
      - E001  Invalid key name (not a valid shell identifier)
      - E002  Duplicate key
      - W001  Value contains unquoted whitespace
      - W002  Line looks like a comment inside a value (# inside unquoted value)
    """
    if not env_path.exists():
        raise LintError(f"File not found: {env_path}")

    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise LintError(str(exc)) from exc

    issues: List[LintIssue] = []
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            issues.append(LintIssue(lineno, "E003", f"Missing '=' in line: {stripped!r}"))
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()

        if not _VALID_KEY_RE.match(key):
            issues.append(LintIssue(lineno, "E001", f"Invalid key name: {key!r}"))

        if key in seen_keys:
            issues.append(
                LintIssue(lineno, "E002", f"Duplicate key {key!r} (first seen on line {seen_keys[key]})")
            )
        else:
            seen_keys[key] = lineno

        is_quoted = (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        )
        if not is_quoted:
            if re.search(r'\s', value):
                issues.append(LintIssue(lineno, "W001", f"Unquoted whitespace in value for {key!r}"))
            if "#" in value:
                issues.append(LintIssue(lineno, "W002", f"Inline comment may be misinterpreted in value for {key!r}"))

    return issues
