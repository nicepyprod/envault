"""Tests for envault.env_merge"""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock, unlock
from envault.env_merge import MergeError, merge_vaults, MergeResult


PASS_A = "passA"
PASS_B = "passB"
PASS_OUT = "passOut"


@pytest.fixture()
def base_vault(tmp_path: Path) -> Path:
    p = tmp_path / "base.vault"
    lock(p, "KEY1=alpha\nKEY2=beta\nSHARED=base_value\n", PASS_A)
    return p


@pytest.fixture()
def other_vault(tmp_path: Path) -> Path:
    p = tmp_path / "other.vault"
    lock(p, "KEY3=gamma\nSHARED=other_value\n", PASS_B)
    return p


@pytest.fixture()
def output_path(tmp_path: Path) -> Path:
    return tmp_path / "merged.vault"


def test_merge_adds_new_keys(base_vault, other_vault, output_path):
    result = merge_vaults(base_vault, PASS_A, other_vault, PASS_B,
                          output_path, PASS_OUT, strategy="ours")
    assert "KEY3" in result.added
    text = unlock(output_path, PASS_OUT)
    assert "KEY3=gamma" in text


def test_merge_strategy_ours_keeps_base(base_vault, other_vault, output_path):
    result = merge_vaults(base_vault, PASS_A, other_vault, PASS_B,
                          output_path, PASS_OUT, strategy="ours")
    assert "SHARED" in result.conflicts
    assert "SHARED" not in result.overwritten
    text = unlock(output_path, PASS_OUT)
    assert "SHARED=base_value" in text


def test_merge_strategy_theirs_overwrites(base_vault, other_vault, output_path):
    result = merge_vaults(base_vault, PASS_A, other_vault, PASS_B,
                          output_path, PASS_OUT, strategy="theirs")
    assert "SHARED" in result.overwritten
    text = unlock(output_path, PASS_OUT)
    assert "SHARED=other_value" in text


def test_merge_strategy_error_raises_on_conflict(base_vault, other_vault, output_path):
    with pytest.raises(MergeError, match="Conflict on key 'SHARED'"):
        merge_vaults(base_vault, PASS_A, other_vault, PASS_B,
                     output_path, PASS_OUT, strategy="error")


def test_merge_no_conflict_succeeds(tmp_path, output_path):
    v1 = tmp_path / "v1.vault"
    v2 = tmp_path / "v2.vault"
    lock(v1, "A=1\n", PASS_A)
    lock(v2, "B=2\n", PASS_B)
    result = merge_vaults(v1, PASS_A, v2, PASS_B, output_path, PASS_OUT)
    assert result.conflicts == []
    text = unlock(output_path, PASS_OUT)
    assert "A=1" in text
    assert "B=2" in text


def test_merge_missing_base_raises(tmp_path, other_vault, output_path):
    with pytest.raises(MergeError, match="Base vault not found"):
        merge_vaults(tmp_path / "nope.vault", PASS_A, other_vault, PASS_B,
                     output_path, PASS_OUT)


def test_merge_missing_other_raises(base_vault, tmp_path, output_path):
    with pytest.raises(MergeError, match="Other vault not found"):
        merge_vaults(base_vault, PASS_A, tmp_path / "nope.vault", PASS_B,
                     output_path, PASS_OUT)


def test_merge_preserves_base_keys(base_vault, other_vault, output_path):
    merge_vaults(base_vault, PASS_A, other_vault, PASS_B,
                 output_path, PASS_OUT, strategy="ours")
    text = unlock(output_path, PASS_OUT)
    assert "KEY1=alpha" in text
    assert "KEY2=beta" in text
