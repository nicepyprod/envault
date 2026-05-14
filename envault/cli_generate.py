"""CLI subcommands for envault generate."""

import argparse
import sys

from envault.env_generate import GenerateError, generate_into_vault
from envault.cli import _read_passphrase


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate a random value for a key inside a vault."""
    passphrase = _read_passphrase("Vault passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1

    try:
        value = generate_into_vault(
            vault_path=args.vault,
            passphrase=passphrase,
            key=args.key,
            length=args.length,
            charset=args.charset,
            overwrite=args.overwrite,
        )
    except GenerateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.print_value:
        print(value)
    else:
        print(f"Generated value stored for key '{args.key}'.")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "generate",
        help="Generate a random secret value for a key in the vault",
    )
    p.add_argument("vault", help="Path to the encrypted vault file")
    p.add_argument("key", help="Environment variable name to generate a value for")
    p.add_argument(
        "--length",
        type=int,
        default=32,
        help="Length of the generated value (default: 32)",
    )
    p.add_argument(
        "--charset",
        default="alphanumeric",
        choices=["hex", "alphanumeric", "ascii", "numeric"],
        help="Character set to use (default: alphanumeric)",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the key if it already exists",
    )
    p.add_argument(
        "--print-value",
        dest="print_value",
        action="store_true",
        help="Print the generated value to stdout",
    )
    p.set_defaults(func=cmd_generate)
