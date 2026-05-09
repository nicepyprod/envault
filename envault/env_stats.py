"""Statistics and summary reporting for vault files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.vault import unlock


class StatsError(Exception):
    """Raised when stats collection fails."""


@dataclass
class VaultStats:
    total_keys: int = 0
    empty_values: int = 0
    duplicate_keys: int = 0
    key_lengths: List[int] = field(default_factory=list)
    value_lengths: List[int] = field(default_factory=list)
    patterns: Dict[str, int] = field(default_factory=dict)

    @property
    def avg_key_length(self) -> float:
        return sum(self.key_lengths) / len(self.key_lengths) if self.key_lengths else 0.0

    @property
    def avg_value_length(self) -> float:
        return sum(self.value_lengths) / len(self.value_lengths) if self.value_lengths else 0.0

    def summary(self) -> str:
        lines = [
            f"Total keys      : {self.total_keys}",
            f"Empty values    : {self.empty_values}",
            f"Duplicate keys  : {self.duplicate_keys}",
            f"Avg key length  : {self.avg_key_length:.1f}",
            f"Avg value length: {self.avg_value_length:.1f}",
        ]
        if self.patterns:
            lines.append("Prefix counts   :")
            for prefix, count in sorted(self.patterns.items()):
                lines.append(f"  {prefix}: {count}")
        return "\n".join(lines)


_PREFIX_RE = re.compile(r'^([A-Z][A-Z0-9]*)_')


def compute_stats(vault_path: Path, passphrase: str) -> VaultStats:
    """Decrypt *vault_path* and return a :class:`VaultStats` summary."""
    if not vault_path.exists():
        raise StatsError(f"Vault not found: {vault_path}")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise StatsError(f"Failed to decrypt vault: {exc}") from exc

    seen_keys: Dict[str, int] = {}
    stats = VaultStats()

    for raw_line in plaintext.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        seen_keys[key] = seen_keys.get(key, 0) + 1
        stats.key_lengths.append(len(key))
        stats.value_lengths.append(len(value))
        if value == "":
            stats.empty_values += 1

        m = _PREFIX_RE.match(key)
        if m:
            prefix = m.group(1)
            stats.patterns[prefix] = stats.patterns.get(prefix, 0) + 1

    stats.total_keys = len(seen_keys)
    stats.duplicate_keys = sum(1 for c in seen_keys.values() if c > 1)
    return stats
