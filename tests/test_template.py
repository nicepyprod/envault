"""Tests for envault.template"""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.template import TemplateError, render_template


PASSPHRASE = "test-passphrase"
ENV_CONTENT = "DB_URL=postgres://localhost/mydb\nSECRET_KEY=supersecret\nDEBUG=false\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    return vault


@pytest.fixture()
def template_file(tmp_path: Path) -> Path:
    tpl = tmp_path / "config.tmpl"
    tpl.write_text("url={{ DB_URL }}\nkey={{ SECRET_KEY }}\n")
    return tpl


def test_render_substitutes_known_keys(vault_file: Path, template_file: Path) -> None:
    result = render_template(template_file, vault_file, PASSPHRASE)
    assert "postgres://localhost/mydb" in result
    assert "supersecret" in result


def test_render_to_output_file(vault_file: Path, template_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "config.rendered"
    render_template(template_file, vault_file, PASSPHRASE, output_path=out)
    assert out.exists()
    content = out.read_text()
    assert "postgres://localhost/mydb" in content


def test_render_strict_raises_on_missing_key(vault_file: Path, tmp_path: Path) -> None:
    tpl = tmp_path / "bad.tmpl"
    tpl.write_text("x={{ NONEXISTENT_KEY }}\n")
    with pytest.raises(TemplateError, match="NONEXISTENT_KEY"):
        render_template(tpl, vault_file, PASSPHRASE, strict=True)


def test_render_lenient_replaces_missing_with_empty(vault_file: Path, tmp_path: Path) -> None:
    tpl = tmp_path / "lenient.tmpl"
    tpl.write_text("x={{ NONEXISTENT_KEY }}\n")
    result = render_template(tpl, vault_file, PASSPHRASE, strict=False)
    assert result == "x=\n"


def test_render_missing_template_raises(vault_file: Path, tmp_path: Path) -> None:
    missing = tmp_path / "ghost.tmpl"
    with pytest.raises(TemplateError, match="Template file not found"):
        render_template(missing, vault_file, PASSPHRASE)


def test_render_missing_vault_raises(tmp_path: Path) -> None:
    tpl = tmp_path / "t.tmpl"
    tpl.write_text("{{ DB_URL }}")
    missing_vault = tmp_path / "no.vault"
    with pytest.raises(TemplateError, match="Vault file not found"):
        render_template(tpl, missing_vault, PASSPHRASE)


def test_render_wrong_passphrase_raises(vault_file: Path, template_file: Path) -> None:
    with pytest.raises(TemplateError, match="Failed to unlock vault"):
        render_template(template_file, vault_file, "wrong-passphrase")


def test_render_preserves_non_placeholder_text(vault_file: Path, tmp_path: Path) -> None:
    tpl = tmp_path / "mixed.tmpl"
    tpl.write_text("# static comment\nurl={{ DB_URL }}\nend\n")
    result = render_template(tpl, vault_file, PASSPHRASE)
    assert result.startswith("# static comment\n")
    assert result.endswith("end\n")
