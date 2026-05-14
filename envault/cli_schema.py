"""CLI commands for schema-based vault validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.cli import _read_passphrase
from envault.env_schema import SchemaError, validate_vault


def cmd_schema_validate(args: argparse.Namespace) -> int:
    """Validate a vault against a JSON schema file."""
    vault_path = Path(args.vault)
    schema_path = Path(args.schema)
    passphrase = _read_passphrase("Passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty.", file=sys.stderr)
        return 1
    try:
        result = validate_vault(vault_path, passphrase, schema_path)
    except SchemaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(result.summary())
    return 0 if result.ok else 1


def cmd_schema_check_file(args: argparse.Namespace) -> int:
    """Check that a schema file is valid (parseable and well-formed)."""
    schema_path = Path(args.schema)
    try:
        from envault.env_schema import load_schema
        schema = load_schema(schema_path)
    except SchemaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    key_count = len(schema)
    print(f"Schema OK — {key_count} key definition(s) found in '{schema_path}'.")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # schema validate
    p_validate = subparsers.add_parser(
        "schema-validate",
        help="Validate a vault's contents against a JSON schema.",
    )
    p_validate.add_argument("vault", help="Path to the encrypted vault file.")
    p_validate.add_argument("schema", help="Path to the JSON schema file.")
    p_validate.set_defaults(func=cmd_schema_validate)

    # schema check
    p_check = subparsers.add_parser(
        "schema-check",
        help="Verify that a schema file is syntactically valid.",
    )
    p_check.add_argument("schema", help="Path to the JSON schema file.")
    p_check.set_defaults(func=cmd_schema_check_file)
