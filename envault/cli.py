"""Command-line interface for envault."""

import argparse
import getpass
import sys
from pathlib import Path

from envault.vault import lock, unlock
from envault.sync import push, pull, SyncError


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_lock(args: argparse.Namespace) -> None:
    """Encrypt a .env file into a vault file."""
    passphrase = _read_passphrase(confirm=True)
    src = Path(args.env_file)
    dst = Path(args.output) if args.output else src.with_suffix(".env.enc")
    lock(src, dst, passphrase)
    print(f"[envault] Locked {src} -> {dst}")

    if args.push:
        try:
            push(dst, message=f"chore: lock {dst.name}")
            print(f"[envault] Pushed {dst} to remote.")
        except SyncError as exc:
            print(f"[envault] Warning: push failed: {exc}", file=sys.stderr)


def cmd_unlock(args: argparse.Namespace) -> None:
    """Decrypt a vault file back to a .env file."""
    passphrase = _read_passphrase(confirm=False)
    src = Path(args.vault_file)
    dst = Path(args.output) if args.output else src.with_suffix("").with_suffix(".env")
    unlock(src, dst, passphrase)
    print(f"[envault] Unlocked {src} -> {dst}")


def cmd_push(args: argparse.Namespace) -> None:
    """Push an already-locked vault file to the remote git repository."""
    vault_file = Path(args.vault_file)
    if not vault_file.exists():
        print(f"[envault] Error: {vault_file} does not exist.", file=sys.stderr)
        sys.exit(1)
    try:
        push(vault_file, message=args.message or f"chore: update {vault_file.name}")
        print(f"[envault] Pushed {vault_file} to remote.")
    except SyncError as exc:
        print(f"[envault] Push failed: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_pull(args: argparse.Namespace) -> None:
    """Pull the latest vault file from the remote git repository."""
    repo_root = Path(args.repo_dir) if args.repo_dir else Path.cwd()
    try:
        pull(repo_root)
        print(f"[envault] Pulled latest changes into {repo_root}.")
    except SyncError as exc:
        print(f"[envault] Pull failed: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_passphrase(confirm: bool = False) -> str:
    passphrase = getpass.getpass("Passphrase: ")
    if confirm:
        second = getpass.getpass("Confirm passphrase: ")
        if passphrase != second:
            print("[envault] Error: passphrases do not match.", file=sys.stderr)
            sys.exit(1)
    return passphrase


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Lightweight .env secret manager with git sync.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # lock
    p_lock = sub.add_parser("lock", help="Encrypt a .env file.")
    p_lock.add_argument("env_file", help="Path to the plaintext .env file.")
    p_lock.add_argument("-o", "--output", help="Destination vault file path.")
    p_lock.add_argument(
        "--push", action="store_true", help="Push the vault file after locking."
    )
    p_lock.set_defaults(func=cmd_lock)

    # unlock
    p_unlock = sub.add_parser("unlock", help="Decrypt a vault file.")
    p_unlock.add_argument("vault_file", help="Path to the encrypted vault file.")
    p_unlock.add_argument("-o", "--output", help="Destination .env file path.")
    p_unlock.set_defaults(func=cmd_unlock)

    # push
    p_push = sub.add_parser("push", help="Push vault file to remote git repo.")
    p_push.add_argument("vault_file", help="Path to the encrypted vault file.")
    p_push.add_argument("-m", "--message", help="Custom commit message.", default="")
    p_push.set_defaults(func=cmd_push)

    # pull
    p_pull = sub.add_parser("pull", help="Pull latest vault from remote git repo.")
    p_pull.add_argument(
        "--repo-dir", dest="repo_dir", help="Repository root (default: cwd)."
    )
    p_pull.set_defaults(func=cmd_pull)

    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
