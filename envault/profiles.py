"""Profile management for envault — allows multiple named vaults (e.g. dev, staging, prod)."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PROFILE = "default"
PROFILES_FILE = ".envault_profiles.json"


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def _profiles_path(base_dir: Path) -> Path:
    return base_dir / PROFILES_FILE


def load_profiles(base_dir: Path) -> dict:
    """Load the profiles config from *base_dir*. Returns empty dict if not found."""
    path = _profiles_path(base_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ProfileError(f"Corrupt profiles file: {path}") from exc


def save_profiles(base_dir: Path, profiles: dict) -> None:
    """Persist *profiles* dict to *base_dir*."""
    _profiles_path(base_dir).write_text(json.dumps(profiles, indent=2))


def add_profile(base_dir: Path, name: str, env_file: str, vault_file: str) -> None:
    """Register a new profile. Raises ProfileError if *name* already exists."""
    profiles = load_profiles(base_dir)
    if name in profiles:
        raise ProfileError(f"Profile '{name}' already exists.")
    profiles[name] = {"env_file": env_file, "vault_file": vault_file}
    save_profiles(base_dir, profiles)


def remove_profile(base_dir: Path, name: str) -> None:
    """Remove a profile by *name*. Raises ProfileError if not found."""
    profiles = load_profiles(base_dir)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' not found.")
    del profiles[name]
    save_profiles(base_dir, profiles)


def get_profile(base_dir: Path, name: str) -> dict:
    """Return config dict for *name*. Raises ProfileError if not found."""
    profiles = load_profiles(base_dir)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' not found.")
    return profiles[name]


def list_profiles(base_dir: Path) -> list[str]:
    """Return sorted list of profile names."""
    return sorted(load_profiles(base_dir).keys())
