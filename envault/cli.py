"""Entry point for the envault CLI."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault import vault
from envault.sync import SyncError, push, pull
import envault.cli_profiles as cli_profiles
import envault.cli_rotate as cli_rotate
import envault.cli_export as cli_export
import envault.cli_snapshot as cli_snapshot
import envault.cli_template as cli_template
import envault.cli_diff as cli_diff
import envault.cli_lint as cli_lint


def _read_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_lock(args: argparse.Namespace) -> int:
    passphrase = _read_passphrase("Passphrase: ")
    confirm = _read_passphrase("Confirm passphrase: ")
    if passphrase != confirm:
        print("error: passphrases do not match", file=sys.stderr)
        return 1
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1
    vault.lock(Path(args.env_file), Path(args.vault_file), passphrase)
    print(f"Locked {args.env_file} → {args.vault_file}")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    passphrase = _read_passphrase("Passphrase: ")
    try:
        vault.unlock(Path(args.vault_file), Path(args.env_file), passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Unlocked {args.vault_file} → {args.env_file}")
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    try:
        push(Path(args.vault_file), args.message)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    try:
        pull()
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Lightweight .env secret manager",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # lock
    p_lock = sub.add_parser("lock", help="Encrypt .env → vault file")
    p_lock.add_argument("--env-file", default=".env")
    p_lock.add_argument("--vault-file", default=".env.vault")
    p_lock.set_defaults(func=cmd_lock)

    # unlock
    p_unlock = sub.add_parser("unlock", help="Decrypt vault file → .env")
    p_unlock.add_argument("--vault-file", default=".env.vault")
    p_unlock.add_argument("--env-file", default=".env")
    p_unlock.set_defaults(func=cmd_unlock)

    # push
    p_push = sub.add_parser("push", help="Commit and push vault to git remote")
    p_push.add_argument("--vault-file", default=".env.vault")
    p_push.add_argument("-m", "--message", default=None)
    p_push.set_defaults(func=cmd_push)

    # pull
    p_pull = sub.add_parser("pull", help="Pull latest vault from git remote")
    p_pull.set_defaults(func=cmd_pull)

    # register feature subcommands
    cli_profiles.register_subcommands(sub)
    cli_rotate.register_subcommands(sub)
    cli_export.register_subcommands(sub)
    cli_snapshot.register_subcommands(sub)
    cli_template.register_subcommands(sub)
    cli_diff.register_subcommands(sub)
    cli_lint.register_subcommands(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
