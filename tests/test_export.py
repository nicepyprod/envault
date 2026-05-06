"""Tests for envault.export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.vault import lock
from envault.export import ExportError, export_vault


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=s3cr3t\n"
PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    vault = tmp_path / ".env.vault"
    env.write_text(ENV_CONTENT, encoding="utf-8")
    lock(env, vault, PASSPHRASE)
    return vault


def test_export_dotenv_roundtrip(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="dotenv")
    assert "DB_HOST=localhost" in result
    assert "SECRET_KEY=s3cr3t" in result


def test_export_json_format(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"
    assert data["SECRET_KEY"] == "s3cr3t"


def test_export_shell_format(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="shell")
    assert "export DB_HOST=localhost" in result
    assert "export SECRET_KEY=s3cr3t" in result


def test_export_to_output_file(vault_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "exported.env"
    export_vault(vault_file, PASSPHRASE, fmt="dotenv", output_file=out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "DB_HOST=localhost" in content


def test_export_unknown_format_raises(vault_file: Path) -> None:
    with pytest.raises(ExportError, match="Unknown format"):
        export_vault(vault_file, PASSPHRASE, fmt="xml")


def test_export_wrong_passphrase_raises(vault_file: Path) -> None:
    with pytest.raises(Exception):
        export_vault(vault_file, "wrong-passphrase", fmt="dotenv")


def test_tmp_file_cleaned_up_on_success(vault_file: Path) -> None:
    export_vault(vault_file, PASSPHRASE, fmt="dotenv")
    tmp = vault_file.with_suffix(".env.tmp")
    assert not tmp.exists()


def test_tmp_file_cleaned_up_on_failure(vault_file: Path) -> None:
    with pytest.raises(Exception):
        export_vault(vault_file, "bad-pass", fmt="dotenv")
    tmp = vault_file.with_suffix(".env.tmp")
    assert not tmp.exists()
