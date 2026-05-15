"""CLI subcommands for placeholder resolution."""

from __future__ import annotations

import argparse
import sys

from envault.cli import _read_passphrase
from envault.env_placeholder import PlaceholderError, find_placeholders, resolve_placeholders
from envault.vault import unlock


def cmd_placeholder_resolve(args: argparse.Namespace) -> int:
    """Resolve all placeholders and print the expanded env."""
    passphrase = _read_passphrase(args)
    if not passphrase:
        print("Error: passphrase must not be empty.", file=sys.stderr)
        return 1
    try:
        result = resolve_placeholders(args.vault, passphrase)
    except PlaceholderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result.cycles:
        print(f"Warning: cyclic references in {', '.join(result.cycles)}", file=sys.stderr)
    if result.unresolved:
        print(f"Warning: unresolved references in {', '.join(result.unresolved)}", file=sys.stderr)

    for key, value in sorted(result.resolved.items()):
        print(f"{key}={value}")
    return 0 if result.ok else 2


def cmd_placeholder_list(args: argparse.Namespace) -> int:
    """List all keys that contain placeholder references."""
    passphrase = _read_passphrase(args)
    if not passphrase:
        print("Error: passphrase must not be empty.", file=sys.stderr)
        return 1
    try:
        raw = unlock(args.vault, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: could not unlock vault: {exc}", file=sys.stderr)
        return 1

    env = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()

    refs = find_placeholders(env)
    if not refs:
        print("No placeholders found.")
        return 0
    for key, targets in sorted(refs.items()):
        print(f"{key} -> {', '.join(targets)}")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # resolve
    p_resolve = subparsers.add_parser(
        "placeholder-resolve", help="Expand all ${KEY} placeholders in the vault"
    )
    p_resolve.add_argument("vault", help="Path to encrypted vault file")
    p_resolve.add_argument("--passphrase", default=None)
    p_resolve.set_defaults(func=cmd_placeholder_resolve)

    # list
    p_list = subparsers.add_parser(
        "placeholder-list", help="List keys that contain placeholder references"
    )
    p_list.add_argument("vault", help="Path to encrypted vault file")
    p_list.add_argument("--passphrase", default=None)
    p_list.set_defaults(func=cmd_placeholder_list)
