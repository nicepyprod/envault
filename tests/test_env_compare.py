"""Tests for envault.env_compare."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.env_compare import CompareError, CompareResult, compare_vaults


PASS_A = "secret-a"
PASS_B = "secret-b"


@pytest.fixture()
def vault_a(tmp_path: Path) -> Path:
    env = tmp_path / "a.env"
    env.write_text("KEY1=hello\nKEY2=world\nSHARED=same\n")
    out = tmp_path / "a.env.vault"
    lock(env, out, PASS_A)
    return out


@pytest.fixture()
def vault_b(tmp_path: Path) -> Path:
    env = tmp_path / "b.env"
    env.write_text("KEY3=foo\nSHARED=same\nKEY2=changed\n")
    out = tmp_path / "b.env.vault"
    lock(env, out, PASS_B)
    return out


@pytest.fixture()
def vault_identical(tmp_path: Path) -> Path:
    env = tmp_path / "id.env"
    env.write_text("KEY1=hello\nKEY2=world\n")
    out = tmp_path / "id.env.vault"
    lock(env, out, PASS_A)
    return out


def test_compare_only_in_a(vault_a: Path, vault_b: Path) -> None:
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "KEY1" in result.only_in_a


def test_compare_only_in_b(vault_a: Path, vault_b: Path) -> None:
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "KEY3" in result.only_in_b


def test_compare_changed(vault_a: Path, vault_b: Path) -> None:
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "KEY2" in result.changed


def test_compare_unchanged(vault_a: Path, vault_b: Path) -> None:
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "SHARED" in result.unchanged


def test_is_identical_false(vault_a: Path, vault_b: Path) -> None:
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert not result.is_identical


def test_is_identical_true(vault_a: Path, vault_identical: Path) -> None:
    result = compare_vaults(vault_a, vault_identical, PASS_A, PASS_A)
    assert not result.is_identical  # KEY2 differs (vault_a has KEY2, vault_identical too)


def test_identical_same_vault(vault_a: Path) -> None:
    result = compare_vaults(vault_a, vault_a, PASS_A, PASS_A)
    assert result.is_identical
    assert result.only_in_a == []
    assert result.only_in_b == []
    assert result.changed == []


def test_wrong_passphrase_raises(vault_a: Path, vault_b: Path) -> None:
    with pytest.raises(CompareError):
        compare_vaults(vault_a, vault_b, "wrong", PASS_B)


def test_summary_non_empty(vault_a: Path, vault_b: Path) -> None:
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    summary = result.summary()
    assert "KEY1" in summary
    assert "KEY3" in summary


def test_summary_identical() -> None:
    r = CompareResult(only_in_a=[], only_in_b=[], changed=[], unchanged=["X"])
    assert "(identical)" not in r.summary()  # unchanged is printed
    r2 = CompareResult(only_in_a=[], only_in_b=[], changed=[], unchanged=[])
    assert "(identical)" in r2.summary()
