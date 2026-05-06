"""Audit log for envault operations (lock, unlock, rotate, push, pull)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_LOG_FILENAME = ".envault_audit.log"


class AuditError(Exception):
    """Raised when an audit log operation fails."""


def _audit_path(base_dir: Optional[Path] = None) -> Path:
    root = base_dir if base_dir is not None else Path.cwd()
    return root / AUDIT_LOG_FILENAME


def record(
    action: str,
    target: str,
    success: bool,
    detail: str = "",
    base_dir: Optional[Path] = None,
) -> None:
    """Append a single audit entry to the log file.

    Each entry is a JSON object on its own line (newline-delimited JSON).
    """
    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "action": action,
        "target": str(target),
        "success": success,
        "detail": detail,
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    }
    log_path = _audit_path(base_dir)
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        raise AuditError(f"Cannot write audit log {log_path}: {exc}") from exc


def read_log(base_dir: Optional[Path] = None) -> List[dict]:
    """Return all audit entries as a list of dicts (oldest first)."""
    log_path = _audit_path(base_dir)
    if not log_path.exists():
        return []
    entries: List[dict] = []
    try:
        with log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Cannot read audit log {log_path}: {exc}") from exc
    return entries


def clear_log(base_dir: Optional[Path] = None) -> None:
    """Delete the audit log file if it exists."""
    log_path = _audit_path(base_dir)
    try:
        log_path.unlink(missing_ok=True)
    except OSError as exc:
        raise AuditError(f"Cannot clear audit log {log_path}: {exc}") from exc
