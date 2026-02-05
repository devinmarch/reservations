# SSH Keys & Config Guide

## How SSH Keys Work

SSH keys come in pairs:
- **Private key** — stays on your machine. Never share this. This is your identity.
- **Public key** — goes on any server you want to access. Think of it as a lock that only your private key can open.

When you connect, the server checks if your private key matches a public key in its `authorized_keys` file. No passwords involved.

## Generate a Key Pair

```
ssh-keygen -t ed25519 -C "your-email@example.com"
```

- `-t ed25519` — the key type. ed25519 is modern and recommended. You'll also see `rsa` which is older but still common.
- `-C "..."` — a comment/label. Convention is to use your email, but it can be anything. It's just for identification.

It will ask:
1. **File location** — press Enter to accept the default (`~/.ssh/id_ed25519`), or provide a custom path if you want multiple keys
2. **Passphrase** — adds a password to the key itself. Optional but recommended. If someone steals your key file, they still need the passphrase.

This creates two files:
```
~/.ssh/id_ed25519          # private key (never share)
~/.ssh/id_ed25519.pub      # public key (goes on servers)
```

## Give Your Public Key to a Server

### Option 1: ssh-copy-id (easiest)
```
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server-ip
```
This copies your public key to the server's `~/.ssh/authorized_keys` file automatically. You'll need to enter the server password this one time.

### Option 2: Manual
```
# Copy the public key contents
cat ~/.ssh/id_ed25519.pub

# SSH into the server with a password, then:
mkdir -p ~/.ssh
echo "your-public-key-contents-here" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Option 3: During server creation
Most VPS providers (Hetzner, DigitalOcean, etc.) let you paste your public key during setup. The server is created with your key already in place — no password login needed.

## The SSH Config File

Location: `~/.ssh/config` on your local machine.

This file lets you create shortcuts so you don't have to type full SSH commands every time.

### Basic Example
```
Host hetzner
    HostName 100.125.170.128
    User root
```

Now `ssh hetzner` is the same as `ssh root@100.125.170.128`.

### With a Specific Key
```
Host hetzner
    HostName 100.125.170.128
    User root
    IdentityFile ~/.ssh/id_ed25519
```

Useful when you have multiple keys for different servers.

### Multiple Servers
```
Host hetzner
    HostName 100.125.170.128
    User devin
    IdentityFile ~/.ssh/id_ed25519

Host work-server
    HostName 10.0.0.50
    User devin.march
    IdentityFile ~/.ssh/work_key
    Port 2222

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_key
```

### Common Options

| Option | What it does |
|--------|-------------|
| `HostName` | The actual IP or domain to connect to |
| `User` | Username to log in as |
| `IdentityFile` | Path to the private key to use |
| `Port` | SSH port if not the default 22 |

## File Permissions

SSH is strict about permissions. If they're wrong, it will refuse to work.

```
chmod 700 ~/.ssh              # directory: owner only
chmod 600 ~/.ssh/config       # config: owner read/write
chmod 600 ~/.ssh/id_ed25519   # private key: owner read/write
chmod 644 ~/.ssh/id_ed25519.pub  # public key: readable
```

These should be set correctly by default, but if SSH gives you a "permissions too open" error, this is the fix.

## Quick Reference

```
# Generate a key
ssh-keygen -t ed25519 -C "you@email.com"

# Copy public key to a server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server-ip

# View your public key (to paste somewhere)
cat ~/.ssh/id_ed25519.pub

# Test a connection
ssh -v hetzner    # -v for verbose output if troubleshooting
```
