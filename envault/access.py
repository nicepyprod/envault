"""Access control: restrict vault operations to allowed users/hosts."""

from __future__ import annotations

import json
import socket
import getpass
from pathlib import Path
from typing import List, Optional


class AccessError(Exception):
    """Raised when an access control rule is violated."""


def _access_path(base_dir: Path) -> Path:
    return base_dir / ".envault_access.json"


def load_rules(base_dir: Path) -> dict:
    """Load access rules from disk. Returns empty rules if file missing."""
    path = _access_path(base_dir)
    if not path.exists():
        return {"allowed_users": [], "allowed_hosts": []}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AccessError(f"Corrupt access file: {exc}") from exc
    if not isinstance(data, dict):
        raise AccessError("Access file must be a JSON object.")
    data.setdefault("allowed_users", [])
    data.setdefault("allowed_hosts", [])
    return data


def save_rules(base_dir: Path, rules: dict) -> None:
    """Persist access rules to disk."""
    path = _access_path(base_dir)
    path.write_text(json.dumps(rules, indent=2))


def add_user(base_dir: Path, username: str) -> None:
    """Add a username to the allowed list."""
    rules = load_rules(base_dir)
    if username in rules["allowed_users"]:
        raise AccessError(f"User '{username}' already in access list.")
    rules["allowed_users"].append(username)
    save_rules(base_dir, rules)


def remove_user(base_dir: Path, username: str) -> None:
    """Remove a username from the allowed list."""
    rules = load_rules(base_dir)
    if username not in rules["allowed_users"]:
        raise AccessError(f"User '{username}' not in access list.")
    rules["allowed_users"].remove(username)
    save_rules(base_dir, rules)


def add_host(base_dir: Path, hostname: str) -> None:
    """Add a hostname to the allowed list."""
    rules = load_rules(base_dir)
    if hostname in rules["allowed_hosts"]:
        raise AccessError(f"Host '{hostname}' already in access list.")
    rules["allowed_hosts"].append(hostname)
    save_rules(base_dir, rules)


def remove_host(base_dir: Path, hostname: str) -> None:
    """Remove a hostname from the allowed list."""
    rules = load_rules(base_dir)
    if hostname not in rules["allowed_hosts"]:
        raise AccessError(f"Host '{hostname}' not in access list.")
    rules["allowed_hosts"].remove(hostname)
    save_rules(base_dir, rules)


def check_access(base_dir: Path) -> None:
    """Raise AccessError if the current user/host is not permitted.

    If both lists are empty, access is unrestricted.
    """
    rules = load_rules(base_dir)
    allowed_users: List[str] = rules["allowed_users"]
    allowed_hosts: List[str] = rules["allowed_hosts"]

    if not allowed_users and not allowed_hosts:
        return  # unrestricted

    current_user = getpass.getuser()
    current_host = socket.gethostname()

    if allowed_users and current_user not in allowed_users:
        raise AccessError(
            f"User '{current_user}' is not allowed to access this vault."
        )
    if allowed_hosts and current_host not in allowed_hosts:
        raise AccessError(
            f"Host '{current_host}' is not allowed to access this vault."
        )
