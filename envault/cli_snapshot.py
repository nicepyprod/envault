"""CLI subcommands for vault snapshot management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.snapshot import SnapshotError, delete_snapshot, list_snapshots, restore_snapshot, save_snapshot


def cmd_snapshot_save(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    try:
        snap = save_snapshot(vault, label=args.label or None)
        print(f"Snapshot saved: {snap}")
        return 0
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_snapshot_list(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    snaps = list_snapshots(vault)
    if not snaps:
        print("No snapshots found.")
    else:
        for s in snaps:
            print(s.name)
    return 0


def cmd_snapshot_restore(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    snap_path = Path(args.snapshot)
    try:
        restore_snapshot(snap_path, vault)
        print(f"Vault restored from snapshot: {snap_path.name}")
        return 0
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_snapshot_delete(args: argparse.Namespace) -> int:
    snap_path = Path(args.snapshot)
    try:
        delete_snapshot(snap_path)
        print(f"Snapshot deleted: {snap_path.name}")
        return 0
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("snapshot", help="Manage vault snapshots")
    sp = p.add_subparsers(dest="snapshot_cmd", required=True)

    save_p = sp.add_parser("save", help="Save a snapshot of the current vault")
    save_p.add_argument("--vault", default=".env.vault", help="Vault file path")
    save_p.add_argument("--label", default="", help="Optional label for the snapshot")
    save_p.set_defaults(func=cmd_snapshot_save)

    list_p = sp.add_parser("list", help="List available snapshots")
    list_p.add_argument("--vault", default=".env.vault", help="Vault file path")
    list_p.set_defaults(func=cmd_snapshot_list)

    restore_p = sp.add_parser("restore", help="Restore vault from a snapshot")
    restore_p.add_argument("snapshot", help="Path to snapshot file")
    restore_p.add_argument("--vault", default=".env.vault", help="Vault file path")
    restore_p.set_defaults(func=cmd_snapshot_restore)

    delete_p = sp.add_parser("delete", help="Delete a snapshot")
    delete_p.add_argument("snapshot", help="Path to snapshot file")
    delete_p.set_defaults(func=cmd_snapshot_delete)
