"""Pin specific keys to fixed values, preventing them from being overwritten during imports or merges."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class PinError(Exception):
    pass


def _pin_path(vault_file: Path) -> Path:
    return vault_file.with_suffix(".pins.json")


def load_pins(vault_file: Path) -> Dict[str, str]:
    """Return {key: pinned_value} dict. Empty dict if no pin file exists."""
    path = _pin_path(vault_file)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PinError(f"Corrupt pin file: {exc}") from exc
    if not isinstance(data, dict):
        raise PinError("Pin file must contain a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def save_pins(vault_file: Path, pins: Dict[str, str]) -> None:
    path = _pin_path(vault_file)
    path.write_text(json.dumps(pins, indent=2))


def pin_key(vault_file: Path, key: str, value: str) -> None:
    """Pin *key* to *value*. Raises PinError if key is empty."""
    if not key:
        raise PinError("Key must not be empty")
    pins = load_pins(vault_file)
    pins[key] = value
    save_pins(vault_file, pins)


def unpin_key(vault_file: Path, key: str) -> None:
    """Remove pin for *key*. Raises PinError if key is not pinned."""
    pins = load_pins(vault_file)
    if key not in pins:
        raise PinError(f"Key '{key}' is not pinned")
    del pins[key]
    save_pins(vault_file, pins)


def list_pins(vault_file: Path) -> List[str]:
    """Return sorted list of pinned key names."""
    return sorted(load_pins(vault_file).keys())


def apply_pins(vault_file: Path, env_dict: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of *env_dict* with pinned values enforced."""
    pins = load_pins(vault_file)
    result = dict(env_dict)
    result.update(pins)
    return result
