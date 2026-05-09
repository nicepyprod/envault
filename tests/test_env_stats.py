"""Tests for envault.env_stats."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.env_stats import compute_stats, StatsError


PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    vault = tmp_path / ".env.vault"
    env.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_PASSWORD=secret\n"
        "APP_NAME=myapp\n"
        "APP_ENV=production\n"
        "EMPTY_VAL=\n"
    )
    lock(env, vault, PASSPHRASE)
    return vault


def test_compute_stats_total_keys(vault_file: Path) -> None:
    stats = compute_stats(vault_file, PASSPHRASE)
    assert stats.total_keys == 6


def test_compute_stats_empty_values(vault_file: Path) -> None:
    stats = compute_stats(vault_file, PASSPHRASE)
    assert stats.empty_values == 1


def test_compute_stats_no_duplicates(vault_file: Path) -> None:
    stats = compute_stats(vault_file, PASSPHRASE)
    assert stats.duplicate_keys == 0


def test_compute_stats_prefix_counts(vault_file: Path) -> None:
    stats = compute_stats(vault_file, PASSPHRASE)
    assert stats.patterns.get("DB") == 3
    assert stats.patterns.get("APP") == 2


def test_compute_stats_avg_key_length(vault_file: Path) -> None:
    stats = compute_stats(vault_file, PASSPHRASE)
    assert stats.avg_key_length > 0


def test_compute_stats_avg_value_length(vault_file: Path) -> None:
    stats = compute_stats(vault_file, PASSPHRASE)
    assert stats.avg_value_length >= 0


def test_compute_stats_missing_vault(tmp_path: Path) -> None:
    with pytest.raises(StatsError, match="Vault not found"):
        compute_stats(tmp_path / "nonexistent.vault", PASSPHRASE)


def test_compute_stats_wrong_passphrase(vault_file: Path) -> None:
    with pytest.raises(StatsError, match="Failed to decrypt"):
        compute_stats(vault_file, "wrong-passphrase")


def test_summary_contains_expected_fields(vault_file: Path) -> None:
    stats = compute_stats(vault_file, PASSPHRASE)
    summary = stats.summary()
    assert "Total keys" in summary
    assert "Empty values" in summary
    assert "Duplicate keys" in summary
    assert "Avg key length" in summary
    assert "Prefix counts" in summary


def test_duplicate_keys_detected(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    vault = tmp_path / ".env.vault"
    env.write_text("FOO=bar\nFOO=baz\nBAR=qux\n")
    lock(env, vault, PASSPHRASE)
    stats = compute_stats(vault, PASSPHRASE)
    assert stats.duplicate_keys == 1
    assert stats.total_keys == 2
