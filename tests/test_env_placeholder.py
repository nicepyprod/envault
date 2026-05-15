"""Tests for envault.env_placeholder."""

from __future__ import annotations

import pytest

from envault.vault import lock
from envault.env_placeholder import (
    PlaceholderError,
    ResolveResult,
    find_placeholders,
    resolve_placeholders,
    _expand,
)


@pytest.fixture()
def vault_file(tmp_path):
    env_path = tmp_path / ".env"
    vault_path = tmp_path / ".env.vault"
    env_path.write_text(
        "BASE=hello\n"
        "GREETING=${BASE} world\n"
        "FULL=${GREETING}, from ${BASE}\n"
        "PLAIN=no_refs\n"
    )
    lock(str(env_path), str(vault_path), "secret")
    return str(vault_path)


# ---------------------------------------------------------------------------
# find_placeholders
# ---------------------------------------------------------------------------

def test_find_placeholders_detects_refs():
    env = {"A": "hello", "B": "${A} world", "C": "${A} and ${B}"}
    refs = find_placeholders(env)
    assert "A" not in refs
    assert refs["B"] == ["A"]
    assert refs["C"] == ["A", "B"]


def test_find_placeholders_empty():
    assert find_placeholders({}) == {}


def test_find_placeholders_no_refs():
    assert find_placeholders({"X": "plain", "Y": "also_plain"}) == {}


# ---------------------------------------------------------------------------
# _expand (unit)
# ---------------------------------------------------------------------------

def test_expand_simple():
    env = {"A": "hi", "B": "${A} there"}
    assert _expand("B", env, frozenset()) == "hi there"


def test_expand_no_placeholder():
    env = {"A": "plain"}
    assert _expand("A", env, frozenset()) == "plain"


def test_expand_missing_ref_raises():
    env = {"A": "${MISSING}"}
    with pytest.raises(KeyError):
        _expand("A", env, frozenset())


def test_expand_cycle_raises():
    env = {"A": "${B}", "B": "${A}"}
    with pytest.raises(PlaceholderError, match="Cycle"):
        _expand("A", env, frozenset())


# ---------------------------------------------------------------------------
# resolve_placeholders (integration)
# ---------------------------------------------------------------------------

def test_resolve_expands_chain(vault_file):
    result = resolve_placeholders(vault_file, "secret")
    assert result.resolved["BASE"] == "hello"
    assert result.resolved["GREETING"] == "hello world"
    assert result.resolved["FULL"] == "hello world, from hello"
    assert result.resolved["PLAIN"] == "no_refs"


def test_resolve_ok_when_no_issues(vault_file):
    result = resolve_placeholders(vault_file, "secret")
    assert result.ok is True
    assert result.unresolved == []
    assert result.cycles == []


def test_resolve_wrong_passphrase_raises(vault_file):
    with pytest.raises(PlaceholderError, match="unlock"):
        resolve_placeholders(vault_file, "wrong")


def test_resolve_unresolved_key(tmp_path):
    env_path = tmp_path / ".env"
    vault_path = tmp_path / ".env.vault"
    env_path.write_text("A=${DOES_NOT_EXIST}\n")
    lock(str(env_path), str(vault_path), "pw")
    result = resolve_placeholders(str(vault_path), "pw")
    assert "A" in result.unresolved
    assert result.ok is False


def test_resolve_result_str(vault_file):
    result = ResolveResult(resolved={"A": "1"}, unresolved=["B"], cycles=[])
    assert "unresolved" in str(result)
