# Vault Access Control

envault supports optional **user** and **host** allowlists to restrict who can
operate on a vault. Rules are stored in `.envault_access.json` alongside your
other vault files.

## How it works

- If **both** lists are empty, access is **unrestricted** (default behaviour).
- If the `allowed_users` list is non-empty, the current OS user must appear in it.
- If the `allowed_hosts` list is non-empty, the current machine hostname must appear in it.
- Both checks must pass when both lists are populated.

## CLI usage

```bash
# Add the current user to the allowlist
envault access add user alice

# Add a machine to the allowlist
envault access add host build-server

# List current rules
envault access list

# Verify the current user/host has access
envault access check

# Remove an entry
envault access remove user alice
envault access remove host build-server
```

## Programmatic usage

```python
from pathlib import Path
from envault.access import add_user, add_host, check_access, AccessError

base = Path(".")
add_user(base, "alice")
add_host(base, "laptop")

try:
    check_access(base)
except AccessError as e:
    print(f"Denied: {e}")
```

## File format

`.envault_access.json` is a plain JSON file:

```json
{
  "allowed_users": ["alice", "bob"],
  "allowed_hosts": ["laptop", "build-server"]
}
```

> **Tip:** Commit `.envault_access.json` to your git repo so access rules are
> shared across machines automatically.
