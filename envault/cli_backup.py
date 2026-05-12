"""CLI subcommands for vault backup/restore."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.env_backup import BackupError, create_backup, delete_backup, list_backups, restore_backup


def cmd_backup_create(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    try:
        dest = create_backup(vault)
        print(f"Backup created: {dest}")
        return 0
    except BackupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_backup_list(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    backups = list_backups(vault)
    if not backups:
        print("No backups found.")
        return 0
    for bp in backups:
        print(bp.name)
    return 0


def cmd_backup_restore(args: argparse.Namespace) -> int:
    try:
        restore_backup(Path(args.backup), Path(args.vault))
        print(f"Restored {args.backup} -> {args.vault}")
        return 0
    except BackupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_backup_delete(args: argparse.Namespace) -> int:
    try:
        delete_backup(Path(args.backup))
        print(f"Deleted backup: {args.backup}")
        return 0
    except BackupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def register_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # create
    p_create = sub.add_parser("backup-create", help="Create a backup of the vault")
    p_create.add_argument("vault", help="Path to the vault file")
    p_create.set_defaults(func=cmd_backup_create)

    # list
    p_list = sub.add_parser("backup-list", help="List backups for a vault")
    p_list.add_argument("vault", help="Path to the vault file")
    p_list.set_defaults(func=cmd_backup_list)

    # restore
    p_restore = sub.add_parser("backup-restore", help="Restore a vault from a backup")
    p_restore.add_argument("backup", help="Path to the backup file")
    p_restore.add_argument("vault", help="Destination vault path")
    p_restore.set_defaults(func=cmd_backup_restore)

    # delete
    p_del = sub.add_parser("backup-delete", help="Delete a backup file")
    p_del.add_argument("backup", help="Path to the backup file")
    p_del.set_defaults(func=cmd_backup_delete)
