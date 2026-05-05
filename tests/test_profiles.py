"""Tests for envault.profiles."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.profiles import (
    ProfileError,
    add_profile,
    get_profile,
    list_profiles,
    load_profiles,
    remove_profile,
    save_profiles,
    _profiles_path,
    PROFILES_FILE,
)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_profiles_missing_file(base_dir):
    assert load_profiles(base_dir) == {}


def test_load_profiles_corrupt_file(base_dir):
    _profiles_path(base_dir).write_text("not json")
    with pytest.raises(ProfileError, match="Corrupt"):
        load_profiles(base_dir)


def test_save_and_load_roundtrip(base_dir):
    data = {"dev": {"env_file": ".env", "vault_file": ".env.vault"}}
    save_profiles(base_dir, data)
    assert load_profiles(base_dir) == data


def test_add_profile_creates_entry(base_dir):
    add_profile(base_dir, "dev", ".env", ".env.vault")
    profiles = load_profiles(base_dir)
    assert "dev" in profiles
    assert profiles["dev"]["env_file"] == ".env"
    assert profiles["dev"]["vault_file"] == ".env.vault"


def test_add_profile_duplicate_raises(base_dir):
    add_profile(base_dir, "dev", ".env", ".env.vault")
    with pytest.raises(ProfileError, match="already exists"):
        add_profile(base_dir, "dev", ".env2", ".env2.vault")


def test_get_profile_returns_config(base_dir):
    add_profile(base_dir, "staging", ".env.staging", ".env.staging.vault")
    cfg = get_profile(base_dir, "staging")
    assert cfg["env_file"] == ".env.staging"


def test_get_profile_missing_raises(base_dir):
    with pytest.raises(ProfileError, match="not found"):
        get_profile(base_dir, "ghost")


def test_remove_profile(base_dir):
    add_profile(base_dir, "prod", ".env.prod", ".env.prod.vault")
    remove_profile(base_dir, "prod")
    assert "prod" not in load_profiles(base_dir)


def test_remove_profile_missing_raises(base_dir):
    with pytest.raises(ProfileError, match="not found"):
        remove_profile(base_dir, "nonexistent")


def test_list_profiles_sorted(base_dir):
    add_profile(base_dir, "prod", ".env.prod", ".env.prod.vault")
    add_profile(base_dir, "dev", ".env", ".env.vault")
    add_profile(base_dir, "staging", ".env.staging", ".env.staging.vault")
    assert list_profiles(base_dir) == ["dev", "prod", "staging"]


def test_list_profiles_empty(base_dir):
    assert list_profiles(base_dir) == []
