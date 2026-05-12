# Key Groups

Key groups let you label subsets of keys inside a vault and extract them into a
separate, independently encrypted vault file.

## Why use groups?

- Share only the database credentials with the DBA team without exposing app secrets.
- Create environment-specific sub-vaults (e.g. `staging`, `prod`) from a single
  master vault.
- Quickly audit which keys belong to a logical component.

## Commands

### Add / update a group

```bash
envault group-add my.vault db DB_HOST,DB_PORT,DB_USER,DB_PASS
```

The group name is arbitrary. The keys are a comma-separated list of environment
variable names that already exist (or will exist) in the vault.

### Remove a group

```bash
envault group-remove my.vault db
```

This only removes the group definition — the keys remain in the vault.

### List groups

```bash
envault group-list my.vault
```

Example output:

```
app: APP_NAME, APP_ENV, APP_VERSION
db: DB_HOST, DB_PORT, DB_USER, DB_PASS
```

### Extract a group into a new vault

```bash
envault group-extract my.vault db --output db_secrets.vault
```

You will be prompted for the **source** vault passphrase. The resulting vault is
encrypted with the **same passphrase**. Use `envault rotate` afterwards if you
want a different passphrase for the extracted vault.

If `--output` is omitted the file is written next to the source vault with the
group name appended, e.g. `my_db.vault`.

## Storage

Group definitions are stored in a sidecar JSON file next to the vault:

```
my.vault          ← encrypted secrets
my.groups.json    ← group definitions (not sensitive, safe to commit)
```

The groups file is plain JSON and can be committed to your git repository.
