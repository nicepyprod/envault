# Envault Hooks

Envault supports **pre/post hooks** — shell commands that run automatically before or after key operations. This lets you integrate notifications, logging, or validation into your workflow.

## Supported Events

| Event | Triggered |
|---|---|
| `pre_lock` | Before encrypting a `.env` file |
| `post_lock` | After encrypting a `.env` file |
| `pre_unlock` | Before decrypting a vault file |
| `post_unlock` | After decrypting a vault file |
| `pre_push` | Before pushing to the git remote |
| `post_push` | After pushing to the git remote |
| `pre_pull` | Before pulling from the git remote |
| `post_pull` | After pulling from the git remote |

Hooks are stored in `.envault_hooks.json` in your project directory. This file should be added to `.gitignore` if hooks contain machine-specific commands.

## Usage

### Register a hook

```bash
envault hook set post_unlock "echo Vault unlocked on $(hostname)"
envault hook set pre_push "./scripts/validate_secrets.sh"
```

### Remove a hook

```bash
envault hook remove pre_push
```

### List all hooks

```bash
envault hook list
```

Example output:

```
pre_push             ./scripts/validate_secrets.sh
post_unlock          echo Vault unlocked
```

## Hook Failure

If a hook exits with a non-zero status code, the envault operation is **aborted** and an error is printed. This allows hooks to act as guards — for example, preventing a push if a validation script fails.

## Storage

Hooks are stored in `.envault_hooks.json`:

```json
{
  "pre_push": "./scripts/validate.sh",
  "post_unlock": "echo done"
}
```
