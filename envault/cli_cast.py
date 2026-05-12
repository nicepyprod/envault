"""CLI commands for type-casting vault key values."""
from __future__ import annotations

import argparse
import sys

from envault.cli import _read_passphrase
from envault.env_cast import CastError, SUPPORTED_TYPES, cast_key


def cmd_cast(args: argparse.Namespace) -> int:
    """Print a vault key's value cast to the requested type."""
    passphrase = _read_passphrase("Passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1

    try:
        result = cast_key(
            vault_path=args.vault,
            passphrase=passphrase,
            key=args.key,
            to_type=args.type,
        )
    except CastError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Pretty-print dicts / lists coming from json cast
    import json as _json
    if isinstance(result, (dict, list)):
        print(_json.dumps(result, indent=2))
    else:
        print(result)
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "cast",
        help="Read a key from the vault and cast its value to a given type",
    )
    p.add_argument("vault", help="Path to the encrypted vault file")
    p.add_argument("key", help="Environment variable key to read")
    p.add_argument(
        "--type",
        required=True,
        choices=SUPPORTED_TYPES,
        help="Target type for the cast",
    )
    p.set_defaults(func=cmd_cast)
