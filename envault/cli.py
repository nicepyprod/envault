"""Command-line interface for envault.

Provides commands to lock (encrypt) and unlock (decrypt) .env files,
as well as initialise a vault directory for git-based syncing.
"""

import os
import sys
import argparse
import getpass

from envault.vault import lock, unlock


DEFAULT_ENV_FILE = ".env"
DEFAULT_VAULT_FILE = ".env.vault"


def cmd_lock(args: argparse.Namespace) -> int:
    """Encrypt a plaintext .env file and write the vault file."""
    env_path = args.env_file
    vault_path = args.vault_file

    if not os.path.exists(env_path):
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 1

    passphrase = _read_passphrase(confirm=True)

    try:
        lock(env_path, vault_path, passphrase)
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Locked '{env_path}' → '{vault_path}'")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    """Decrypt a vault file and restore the plaintext .env file."""
    vault_path = args.vault_file
    env_path = args.env_file

    if not os.path.exists(vault_path):
        print(f"error: vault file not found: {vault_path}", file=sys.stderr)
        return 1

    passphrase = _read_passphrase(confirm=False)

    try:
        unlock(vault_path, env_path, passphrase)
    except ValueError as exc:
        print(f"error: decryption failed — wrong passphrase? ({exc})", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Unlocked '{vault_path}' → '{env_path}'")
    return 0


def _read_passphrase(confirm: bool) -> str:
    """Prompt the user for a passphrase, optionally asking twice for confirmation."""
    # Allow passphrase injection via environment variable for non-interactive use
    env_pass = os.environ.get("ENVAULT_PASSPHRASE")
    if env_pass is not None:
        return env_pass

    passphrase = getpass.getpass("Passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        sys.exit(1)

    if confirm:
        confirm_pass = getpass.getpass("Confirm passphrase: ")
        if passphrase != confirm_pass:
            print("error: passphrases do not match", file=sys.stderr)
            sys.exit(1)

    return passphrase


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Encrypt and sync .env secrets via a git repo.",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.1.0"
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ---- lock ----
    lock_p = sub.add_parser("lock", help="Encrypt .env → .env.vault")
    lock_p.add_argument(
        "--env-file", default=DEFAULT_ENV_FILE,
        metavar="FILE", help=f"Plaintext env file (default: {DEFAULT_ENV_FILE})"
    )
    lock_p.add_argument(
        "--vault-file", default=DEFAULT_VAULT_FILE,
        metavar="FILE", help=f"Output vault file (default: {DEFAULT_VAULT_FILE})"
    )
    lock_p.set_defaults(func=cmd_lock)

    # ---- unlock ----
    unlock_p = sub.add_parser("unlock", help="Decrypt .env.vault → .env")
    unlock_p.add_argument(
        "--vault-file", default=DEFAULT_VAULT_FILE,
        metavar="FILE", help=f"Vault file to decrypt (default: {DEFAULT_VAULT_FILE})"
    )
    unlock_p.add_argument(
        "--env-file", default=DEFAULT_ENV_FILE,
        metavar="FILE", help=f"Output env file (default: {DEFAULT_ENV_FILE})"
    )
    unlock_p.set_defaults(func=cmd_unlock)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the envault CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
