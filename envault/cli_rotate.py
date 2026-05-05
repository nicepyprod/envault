"""CLI subcommand: envault rotate — change the vault passphrase."""

import argparse
import sys
from pathlib import Path

from .cli import _read_passphrase
from .rotate import RotateError, rotate


def cmd_rotate(args: argparse.Namespace) -> int:
    """Handle the *rotate* subcommand.

    Prompts for the old passphrase, then the new passphrase (twice for
    confirmation), and re-encrypts the vault in place.

    Returns 0 on success, 1 on failure.
    """
    vault_path = Path(args.vault)
    env_path = Path(args.env)

    try:
        old_passphrase = _read_passphrase("Old passphrase: ")
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.", file=sys.stderr)
        return 1

    try:
        new_passphrase = _read_passphrase("New passphrase: ")
        confirm = _read_passphrase("Confirm new passphrase: ")
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.", file=sys.stderr)
        return 1

    if new_passphrase != confirm:
        print("Error: passphrases do not match.", file=sys.stderr)
        return 1

    if not new_passphrase:
        print("Error: new passphrase must not be empty.", file=sys.stderr)
        return 1

    try:
        rotate(
            env_path=env_path,
            vault_path=vault_path,
            old_passphrase=old_passphrase,
            new_passphrase=new_passphrase,
        )
    except RotateError as exc:
        print(f"Rotate failed: {exc}", file=sys.stderr)
        return 1

    print(f"Vault re-encrypted successfully: {vault_path}")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *rotate* subcommand onto *subparsers*."""
    parser = subparsers.add_parser(
        "rotate",
        help="Re-encrypt the vault with a new passphrase.",
    )
    parser.add_argument(
        "--vault",
        default=".env.vault",
        help="Path to the encrypted vault file (default: .env.vault).",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Temporary plaintext .env path used during rotation (default: .env).",
    )
    parser.set_defaults(func=cmd_rotate)
