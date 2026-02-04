# Caddy Basic Auth

## Generate a Password Hash

```bash
caddy hash-password
```

Type your password when prompted. Copy the output hash.

## Single Endpoint, Multiple Users

```
basicauth /admin/* {
    alice $2a$14$hashedpassword1...
    bob $2a$14$hashedpassword2...
}
```

All listed users can access `/admin/` and anything under it.

## Different Users Per Endpoint

```
# Only admins
basicauth /admin/* {
    alice $2a$14$hash1...
}

# Only finance team
basicauth /reports/* {
    bob $2a$14$hash2...
    charlie $2a$14$hash3...
}

# Everyone
basicauth /dashboard/* {
    alice $2a$14$hash1...
    bob $2a$14$hash2...
    charlie $2a$14$hash3...
}
```

Each `basicauth` block is independent.

## Protect Entire Site

```
basicauth * {
    user $2a$14$hash...
}
```

## Apply Changes

After editing the Caddyfile:

```bash
sudo cp config/Caddyfile /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

## Notes

- Passwords must be hashed (never plain text)
- The `/*` means "this path and everything under it"
- Users are defined per-block, so the same user can appear in multiple blocks

## Adding Additional Domains

Point a new domain to the same backend:

```
app.cliffsedgeretreat.ca {
    reverse_proxy localhost:5000
}
```

Caddy automatically handles SSL via Let's Encrypt.

To share config across multiple domains:

```
res.devinmarch.com, app.cliffsedgeretreat.ca {
    reverse_proxy localhost:5000
}
```

Keep domains separate if they need different auth rules.
