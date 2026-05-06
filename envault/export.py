"""Export decrypted vault contents to various formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .vault import unlock


class ExportError(Exception):
    """Raised when an export operation fails."""


FORMATS = ("dotenv", "json", "shell")


def _parse_env_lines(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines, ignoring comments and blank lines."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def export_vault(
    vault_file: Path,
    passphrase: str,
    fmt: str = "dotenv",
    output_file: Path | None = None,
) -> str:
    """Decrypt *vault_file* and serialise its contents as *fmt*.

    Supported formats: ``dotenv``, ``json``, ``shell``.
    If *output_file* is given the result is also written there.
    Returns the serialised string.
    """
    if fmt not in FORMATS:
        raise ExportError(f"Unknown format '{fmt}'. Choose from: {', '.join(FORMATS)}")

    env_path = vault_file.with_suffix(".env.tmp")
    try:
        unlock(vault_file, env_path, passphrase)
        raw = env_path.read_text(encoding="utf-8")
    finally:
        if env_path.exists():
            env_path.unlink()

    pairs = _parse_env_lines(raw)

    if fmt == "dotenv":
        serialised = "\n".join(f"{k}={v}" for k, v in pairs.items()) + "\n"
    elif fmt == "json":
        serialised = json.dumps(pairs, indent=2) + "\n"
    elif fmt == "shell":
        serialised = "\n".join(f"export {k}={v}" for k, v in pairs.items()) + "\n"
    else:  # pragma: no cover
        raise ExportError(f"Unhandled format '{fmt}'")

    if output_file is not None:
        output_file.write_text(serialised, encoding="utf-8")

    return serialised
