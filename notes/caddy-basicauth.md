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

## Different Users Per Endpoint (with Realms)

When you have multiple `basicauth` blocks on the same host, you **must** give each a distinct realm. Otherwise the browser caches credentials under the same realm name and can send the wrong ones for different paths (e.g., toggling a detail row triggers a re-auth prompt).

The syntax is `basicauth <matcher> bcrypt <realm-name>`:

```
@notguest not path /ota*
basicauth @notguest bcrypt admin {
    alice $2a$14$hash1...
}

@ota path /ota*
basicauth @ota bcrypt ota {
    bob $2a$14$hash2...
    charlie $2a$14$hash3...
}
```

- `bcrypt` tells Caddy the hash algorithm (required before the realm name)
- `admin` and `ota` are the realm names — the browser keeps credentials separate per realm
- Without distinct realms, both blocks share a default realm and the browser can get confused

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
- Always use distinct realms when multiple `basicauth` blocks exist on the same host

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
