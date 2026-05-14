"""Generate random secret values for environment keys."""

import secrets
import string

__all__ = ["GenerateError", "generate_value", "generate_into_vault"]

_CHARSETS = {
    "hex": string.hexdigits[:16],
    "alphanumeric": string.ascii_letters + string.digits,
    "ascii": string.ascii_letters + string.digits + string.punctuation,
    "numeric": string.digits,
}


class GenerateError(Exception):
    """Raised when value generation fails."""


def generate_value(length: int = 32, charset: str = "alphanumeric") -> str:
    """Return a cryptographically random string.

    Args:
        length: Number of characters to generate (1–256).
        charset: One of 'hex', 'alphanumeric', 'ascii', 'numeric'.

    Returns:
        A random string of *length* characters.
    """
    if length < 1 or length > 256:
        raise GenerateError(f"length must be between 1 and 256, got {length}")
    if charset not in _CHARSETS:
        raise GenerateError(
            f"unknown charset '{charset}'; choose from {sorted(_CHARSETS)}"
        )
    alphabet = _CHARSETS[charset]
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_into_vault(
    vault_path: str,
    passphrase: str,
    key: str,
    length: int = 32,
    charset: str = "alphanumeric",
    overwrite: bool = False,
) -> str:
    """Generate a random value and store it in an existing vault.

    Returns the generated value so the caller can display it if needed.
    Raises GenerateError if the key already exists and *overwrite* is False.
    """
    from envault.env_edit import set_key, EditError, _parse_env_dict
    from envault.vault import unlock

    plaintext = unlock(vault_path, passphrase)
    existing = _parse_env_dict(plaintext)

    if key in existing and not overwrite:
        raise GenerateError(
            f"key '{key}' already exists; pass overwrite=True to replace it"
        )

    value = generate_value(length=length, charset=charset)
    try:
        set_key(vault_path, passphrase, key, value)
    except EditError as exc:
        raise GenerateError(str(exc)) from exc

    return value
