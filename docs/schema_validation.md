# Schema Validation

envault supports validating the contents of an encrypted vault against a **JSON schema** file, ensuring that required keys are present, values have the correct types, and values conform to patterns or allowed lists.

## Schema File Format

A schema is a plain JSON object where each top-level key corresponds to an environment variable name. Each value is a rule object that can contain:

| Field | Type | Description |
|-------|------|-------------|
| `required` | bool | If `true`, the key must be present in the vault. |
| `type` | string | Expected type: `str`, `int`, `float`, or `bool`. |
| `pattern` | string | A Python `re.fullmatch` pattern the value must satisfy. |
| `allowed` | list | An explicit list of permitted values. |

### Example

```json
{
  "DATABASE_URL": {
    "required": true,
    "type": "str"
  },
  "PORT": {
    "required": true,
    "type": "int"
  },
  "LOG_LEVEL": {
    "required": false,
    "allowed": ["DEBUG", "INFO", "WARNING", "ERROR"]
  },
  "API_KEY": {
    "required": true,
    "pattern": "[A-Za-z0-9_\\-]{16,}"
  }
}
```

## CLI Usage

### Validate a vault

```bash
envault schema-validate .env.vault schema.json
```

You will be prompted for the vault passphrase. The command exits with code `0` on success and `1` if any violations are found.

### Check a schema file

Verify that a schema file is syntactically valid without decrypting any vault:

```bash
envault schema-check schema.json
```

## Programmatic Usage

```python
from pathlib import Path
from envault.env_schema import validate_vault

result = validate_vault(
    vault_path=Path(".env.vault"),
    passphrase="my-secret",
    schema_path=Path("schema.json"),
)

if result.ok:
    print("All checks passed!")
else:
    print(result.summary())
```

## Notes

- Keys present in the vault but **not** listed in the schema are silently ignored.
- The `bool` type accepts `true`, `false`, `1`, `0`, `yes`, and `no` (case-insensitive).
- Schema validation never modifies the vault file.
