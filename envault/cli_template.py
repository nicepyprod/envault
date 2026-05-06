"""CLI subcommands for template rendering."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.cli import _read_passphrase
from envault.template import TemplateError, render_template


def cmd_render(args: argparse.Namespace) -> int:
    """Render a template file using secrets from a vault."""
    passphrase = _read_passphrase(confirm=False)
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1

    template_path = Path(args.template)
    vault_path = Path(args.vault)
    output_path = Path(args.output) if args.output else None
    strict = not args.lenient

    try:
        rendered = render_template(
            template_path=template_path,
            vault_path=vault_path,
            passphrase=passphrase,
            output_path=output_path,
            strict=strict,
        )
    except TemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if output_path is None:
        print(rendered, end="")
    else:
        print(f"Rendered template written to {output_path}")

    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the *render* subcommand to *subparsers*."""
    p = subparsers.add_parser(
        "render",
        help="Render a template file substituting vault secrets for {{ KEY }} placeholders",
    )
    p.add_argument("template", help="Path to the template file")
    p.add_argument(
        "--vault",
        default=".env.vault",
        help="Path to the vault file (default: .env.vault)",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Write rendered output to this file instead of stdout",
    )
    p.add_argument(
        "--lenient",
        action="store_true",
        help="Replace unknown placeholders with empty string instead of raising an error",
    )
    p.set_defaults(func=cmd_render)
