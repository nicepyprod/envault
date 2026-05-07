"""Tests for envault.ttl."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.ttl import (
    TTLError,
    _ttl_path,
    check_ttl,
    clear_ttl,
    get_ttl,
    remaining_seconds,
    set_ttl,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


# ---------------------------------------------------------------------------
# set_ttl / get_ttl
# ---------------------------------------------------------------------------

def test_set_ttl_creates_file(vault_file):
    set_ttl(vault_file, 60)
    assert _ttl_path(vault_file).exists()


def test_set_ttl_returns_future_timestamp(vault_file):
    before = time.time()
    expires = set_ttl(vault_file, 120)
    after = time.time()
    assert before + 120 <= expires <= after + 120


def test_get_ttl_returns_none_when_no_file(vault_file):
    assert get_ttl(vault_file) is None


def test_get_ttl_matches_set_ttl(vault_file):
    expires = set_ttl(vault_file, 300)
    assert get_ttl(vault_file) == pytest.approx(expires, abs=1.0)


def test_set_ttl_zero_raises(vault_file):
    with pytest.raises(TTLError):
        set_ttl(vault_file, 0)


def test_set_ttl_negative_raises(vault_file):
    with pytest.raises(TTLError):
        set_ttl(vault_file, -10)


def test_set_ttl_overwrites_existing(vault_file):
    """Calling set_ttl twice should update the expiry to the latest value."""
    set_ttl(vault_file, 60)
    expires = set_ttl(vault_file, 3600)
    stored = get_ttl(vault_file)
    assert stored == pytest.approx(expires, abs=1.0)


# ---------------------------------------------------------------------------
# clear_ttl
# ---------------------------------------------------------------------------

def test_clear_ttl_removes_file(vault_file):
    set_ttl(vault_file, 60)
    result = clear_ttl(vault_file)
    assert result is True
    assert not _ttl_path(vault_file).exists()


def test_clear_ttl_returns_false_when_no_file(vault_file):
    assert clear_ttl(vault_file) is False


def test_clear_ttl_resets_get_ttl(vault_file):
    """After clearing, get_ttl should return None."""
    set_ttl(vault_file, 60)
    clear_ttl(vault_file)
    assert get_ttl(vault_file) is None


# ---------------------------------------------------------------------------
# check_ttl
# ---------------------------------------------------------------------------

def test_check_ttl_passes_when_no_ttl(vault_file):
    check_ttl(vault_file)  # should not raise


def test_check_ttl_passes_for_future_expiry(vault_file):
    set_ttl(vault_file, 3600)
    check_ttl(vault_file)  # should not raise


def test_check_ttl_raises_for_expired_vault(vault_file):
    ttl_file = _ttl_path(vault_file)
    ttl_file.write_text(
        json.dumps({"expires_at": time.time() - 10}), encoding="utf-8"
    )
    with pytest.raises(TTLError, match="expired"):
        check_ttl(vault_file)


# ---------------------------------------------------------------------------
# remaining_seconds
# ---------------------------------------------------------------------------

def test_remaining_seconds_none_when_no_ttl(vault_file):
    assert remaining_seconds(vault_file) is None


def test_remaining_seconds_positive_for_future(vault_file):
    set_ttl(vault_file, 100)
    rem = remaining_seconds(vault_file)
    assert rem is not None
    assert 0 < rem <= 100


def test_remaining_seconds_negative_when_expired(vault_file):
    """remaining_seconds should return a negative value for an expired vault."""
    ttl_file = _ttl_path(vault_file)
    ttl_file.write_text(
        json.dumps({"expires_at": time.time() - 30}), encoding="utf-8"
    )
    rem = remaining_seconds(vault_file)
    assert rem is not None
    assert rem < 0
