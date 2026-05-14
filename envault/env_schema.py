"""Schema validation for .env vaults — enforce types, required keys, and allowed values."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from envault.vault import unlock


class SchemaError(Exception):
    """Raised when schema operations fail."""


@dataclass
class SchemaViolation:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class SchemaResult:
    violations: list[SchemaViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.ok:
            return "Schema validation passed."
        lines = [f"Schema validation failed ({len(self.violations)} issue(s)):"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


_VALID_TYPES = {"str", "int", "float", "bool"}


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load a JSON schema file. Returns a dict keyed by env-var name."""
    if not schema_path.exists():
        raise SchemaError(f"Schema file not found: {schema_path}")
    try:
        data = json.loads(schema_path.read_text())
    except json.JSONDecodeError as exc:
        raise SchemaError(f"Schema file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaError("Schema must be a JSON object at the top level.")
    return data


def _parse_env_dict(plaintext: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def validate_vault(vault_path: Path, passphrase: str, schema_path: Path) -> SchemaResult:
    """Decrypt vault and validate its contents against a JSON schema."""
    if not vault_path.exists():
        raise SchemaError(f"Vault file not found: {vault_path}")
    schema = load_schema(schema_path)
    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise SchemaError(f"Failed to decrypt vault: {exc}") from exc
    env = _parse_env_dict(plaintext)
    violations: list[SchemaViolation] = []
    for key, rules in schema.items():
        if not isinstance(rules, dict):
            continue
        required = rules.get("required", False)
        if key not in env:
            if required:
                violations.append(SchemaViolation(key, "required key is missing"))
            continue
        value = env[key]
        expected_type = rules.get("type")
        if expected_type:
            if expected_type not in _VALID_TYPES:
                raise SchemaError(f"Unknown type '{expected_type}' for key '{key}'.")
            violations.extend(_check_type(key, value, expected_type))
        pattern = rules.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            violations.append(SchemaViolation(key, f"value does not match pattern '{pattern}'"))
        allowed = rules.get("allowed")
        if allowed is not None and value not in allowed:
            violations.append(SchemaViolation(key, f"value '{value}' not in allowed list"))
    return SchemaResult(violations=violations)


def _check_type(key: str, value: str, expected: str) -> list[SchemaViolation]:
    try:
        if expected == "int":
            int(value)
        elif expected == "float":
            float(value)
        elif expected == "bool":
            if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError
    except ValueError:
        return [SchemaViolation(key, f"value '{value}' cannot be cast to {expected}")]
    return []
