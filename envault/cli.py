"""Main CLI entry point for envault."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault import vault
from envault.sync import SyncError, pull, push
from envault import cli_profiles, cli_rotate, cli_export, cli_diff, cli_snapshot


def _read_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_lock(args: argparse.Namespace) -> int:
    env_file = Path(args.env_file)
    vault_file = Path(args.vault_file)
    if not env_file.exists():
        print(f"error: {env_file} not found", file=sys.stderr)
        return 1
    passphrase = _read_passphrase("Passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1
    vault.lock(env_file, vault_file, passphrase)
    print(f"Locked {env_file} -> {vault_file}")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    vault_file = Path(args.vault_file)
    env_file = Path(args.env_file)
    if not vault_file.exists():
        print(f"error: {vault_file} not found", file=sys.stderr)
        return 1
    passphrase = _read_passphrase("Passphrase: ")
    try:
        vault.unlock(vault_file, env_file, passphrase)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Unlocked {vault_file} -> {env_file}")
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    try:
        push(Path(args.repo), args.message)
        print("Pushed vault to remote.")
        return 0
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_pull(args: argparse.Namespace) -> int:
    try:
        pull(Path(args.repo))
        print("Pulled vault from remote.")
        return 0
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Lightweight .env secret manager",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # lock
    p_lock = sub.add_parser("lock", help="Encrypt .env -> vault")
    p_lock.add_argument("--env-file", default=".env")
    p_lock.add_argument("--vault-file", default=".env.vault")
    p_lock.set_defaults(func=cmd_lock)

    # unlock
    p_unlock = sub.add_parser("unlock", help="Decrypt vault -> .env")
    p_unlock.add_argument("--vault-file", default=".env.vault")
    p_unlock.add_argument("--env-file", default=".env")
    p_unlock.set_defaults(func=cmd_unlock)

    # push
    p_push = sub.add_parser("push", help="Push vault to remote git repo")
    p_push.add_argument("--repo", default=".")
    p_push.add_argument("--message", default="chore: update vault")
    p_push.set_defaults(func=cmd_push)

    # pull
    p_pull = sub.add_parser("pull", help="Pull vault from remote git repo")
    p_pull.add_argument("--repo", default=".")
    p_pull.set_defaults(func=cmd_pull)

    cli_profiles.register_subcommands(sub)
    cli_rotate.register_subcommands(sub)
    cli_export.register_subcommands(sub)
    cli_diff.register_subcommands(sub)
    cli_snapshot.register_subcommands(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        return args.func(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
