"""Template rendering: substitute vault secrets into template files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

from envault.vault import unlock


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def _parse_env_dict(plaintext: str) -> Dict[str, str]:
    """Parse decrypted .env content into a key→value mapping."""
    result: Dict[str, str] = {}
    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def render_template(
    template_path: Path,
    vault_path: Path,
    passphrase: str,
    output_path: Path | None = None,
    strict: bool = True,
) -> str:
    """Render *template_path* by substituting ``{{ KEY }}`` placeholders.

    Secrets are read from *vault_path* using *passphrase*.  When *strict* is
    ``True`` (default) any placeholder with no matching vault key raises
    :class:`TemplateError`.  Returns the rendered string and optionally writes
    it to *output_path*.
    """
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")
    if not vault_path.exists():
        raise TemplateError(f"Vault file not found: {vault_path}")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise TemplateError(f"Failed to unlock vault: {exc}") from exc

    secrets = _parse_env_dict(plaintext)
    template_text = template_path.read_text(encoding="utf-8")

    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key not in secrets:
            if strict:
                missing.append(key)
                return match.group(0)
            return ""
        return secrets[key]

    rendered = _PLACEHOLDER_RE.sub(_replace, template_text)

    if missing:
        raise TemplateError(
            f"Template references undefined vault keys: {', '.join(sorted(missing))}"
        )

    if output_path is not None:
        output_path.write_text(rendered, encoding="utf-8")

    return rendered
