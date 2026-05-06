"""CLI sub-commands for the export feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli import _read_passphrase
from .export import ExportError, FORMATS, export_vault


def cmd_export(args: argparse.Namespace) -> int:
    """Handle the ``envault export`` sub-command."""
    vault_file = Path(args.vault)
    if not vault_file.exists():
        print(f"error: vault file not found: {vault_file}", file=sys.stderr)
        return 1

    output_file: Path | None = Path(args.output) if args.output else None

    try:
        passphrase = _read_passphrase(confirm=False)
        result = export_vault(
            vault_file=vault_file,
            passphrase=passphrase,
            fmt=args.format,
            output_file=output_file,
        )
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if output_file:
        print(f"Exported to {output_file}")
    else:
        sys.stdout.write(result)

    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the ``export`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "export",
        help="Export decrypted vault contents to dotenv / json / shell format",
    )
    p.add_argument(
        "--vault",
        default=".env.vault",
        help="Path to the vault file (default: .env.vault)",
    )
    p.add_argument(
        "--format",
        choices=FORMATS,
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    p.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    p.set_defaults(func=cmd_export)
