"""CLI subcommand: envault lint"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.lint import LintError, lint_env_file


def cmd_lint(args: argparse.Namespace) -> int:
    """Lint an .env file and report issues."""
    env_path = Path(args.env_file)

    try:
        issues = lint_env_file(env_path)
    except LintError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not issues:
        print(f"✓ No issues found in {env_path}")
        return 0

    error_count = sum(1 for i in issues if i.code.startswith("E"))
    warn_count = sum(1 for i in issues if i.code.startswith("W"))

    for issue in issues:
        prefix = "ERROR" if issue.code.startswith("E") else "WARN "
        print(f"{prefix}  {issue}")

    print(f"\n{len(issues)} issue(s): {error_count} error(s), {warn_count} warning(s).")
    return 1 if error_count > 0 else 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "lint",
        help="Validate a .env file for common issues",
    )
    parser.add_argument(
        "env_file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.set_defaults(func=cmd_lint)
