# envault

> Lightweight .env secret manager that encrypts local environment files and syncs them across machines via a git repo.

---

## Installation

```bash
pip install envault
```

---

## Usage

**Initialize envault in your project:**

```bash
envault init
```

**Encrypt and push your `.env` file:**

```bash
envault push --file .env
```

**Pull and decrypt on another machine:**

```bash
envault pull --file .env
```

**Rotate your encryption key:**

```bash
envault rotate-key
```

Envault stores an encrypted copy of your secrets in a connected git repository. Each machine decrypts locally using a master key stored in `~/.envault/keyring`. Your plaintext secrets never leave your machine unencrypted.

```
my-project/
├── .env              ← local, gitignored
├── .env.vault        ← encrypted, committed to git
└── .envault.toml     ← config, committed to git
```

---

## Configuration

```toml
# .envault.toml
[vault]
repo = "git@github.com:yourname/my-secrets-vault.git"
branch = "main"
algorithm = "AES-256-GCM"
```

---

## License

MIT © 2024 envault contributors