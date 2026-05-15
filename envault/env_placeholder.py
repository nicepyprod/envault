"""Placeholder detection and resolution for vault entries.

A placeholder is a value like ``${OTHER_KEY}`` that references another key
in the same vault.  ``resolve_placeholders`` expands all such references
(up to a fixed depth) and returns a new dict with concrete values.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from envault.vault import unlock

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_MAX_DEPTH = 10


class PlaceholderError(Exception):
    """Raised when placeholder resolution fails."""


@dataclass
class ResolveResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: List[str] = field(default_factory=list)
    cycles: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unresolved and not self.cycles

    def __str__(self) -> str:  # pragma: no cover
        parts = [f"{len(self.resolved)} key(s) resolved"]
        if self.unresolved:
            parts.append(f"unresolved: {', '.join(self.unresolved)}")
        if self.cycles:
            parts.append(f"cycles: {', '.join(self.cycles)}")
        return "; ".join(parts)


def _expand(key: str, env: Dict[str, str], seen: frozenset) -> str:
    """Recursively expand a single key's value."""
    value = env[key]
    if key in seen:
        raise PlaceholderError(f"Cycle detected for key: {key}")
    new_seen = seen | {key}
    depth = len(new_seen)
    if depth > _MAX_DEPTH:
        raise PlaceholderError(f"Max resolution depth ({_MAX_DEPTH}) exceeded")

    def _replace(m: re.Match) -> str:
        ref = m.group(1)
        if ref not in env:
            raise KeyError(ref)
        return _expand(ref, env, new_seen)

    return _REF_RE.sub(_replace, value)


def find_placeholders(env: Dict[str, str]) -> Dict[str, List[str]]:
    """Return a mapping of key -> list of referenced keys."""
    result: Dict[str, List[str]] = {}
    for key, value in env.items():
        refs = _REF_RE.findall(value)
        if refs:
            result[key] = refs
    return result


def resolve_placeholders(vault_path: str, passphrase: str) -> ResolveResult:
    """Decrypt *vault_path* and resolve all ``${KEY}`` placeholders."""
    try:
        raw = unlock(vault_path, passphrase)
    except Exception as exc:  # noqa: BLE001
        raise PlaceholderError(f"Could not unlock vault: {exc}") from exc

    env: Dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()

    result = ResolveResult()
    for key in env:
        try:
            result.resolved[key] = _expand(key, env, frozenset())
        except KeyError as exc:
            result.unresolved.append(key)
            result.resolved[key] = env[key]
        except PlaceholderError:
            result.cycles.append(key)
            result.resolved[key] = env[key]
    return result
