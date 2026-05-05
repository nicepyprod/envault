"""envault — Lightweight .env secret manager."""

from envault.vault import lock, unlock

__all__ = ["lock", "unlock"]
__version__ = "0.1.0"
