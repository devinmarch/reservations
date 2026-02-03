# Caddy Quick Reference

## File Locations

```
/etc/caddy/Caddyfile    # System config (the one Caddy actually uses)
```

## Essential Commands

```bash
# Edit the config
sudo nano /etc/caddy/Caddyfile

# Reload after changes (no downtime)
sudo systemctl reload caddy

# Start / Stop / Restart
sudo systemctl start caddy
sudo systemctl stop caddy
sudo systemctl restart caddy

# Check status
sudo systemctl status caddy

# View logs
sudo journalctl -u caddy --no-pager -n 50

# Test config for errors (without applying)
caddy validate --config /etc/caddy/Caddyfile
```

## Caddyfile Syntax Basics

```
domain.com {
    # directives go here
}
```

- Each site block starts with the address (domain, IP, or port)
- Directives are indented inside the block
- Caddy auto-provisions HTTPS certificates via Let's Encrypt

## Common Patterns

### Reverse Proxy

```
example.com {
    reverse_proxy localhost:3000
}
```

### Reverse Proxy with Path

```
example.com {
    reverse_proxy /api/* localhost:8080
    reverse_proxy localhost:3000
}
```

### Static Files

```
example.com {
    root * /var/www/mysite
    file_server
}
```

### Basic Authentication

```
example.com {
    basicauth {
        username $2a$14$hashedpasswordhere
    }
    reverse_proxy localhost:3000
}
```

Generate password hash:
```bash
caddy hash-password
```

### Protect Only Certain Paths

```
example.com {
    basicauth /admin/* {
        admin $2a$14$hashedpasswordhere
    }
    reverse_proxy localhost:3000
}
```

### Multiple Domains, Same Site

```
example.com, www.example.com {
    reverse_proxy localhost:3000
}
```

### Redirect WWW to Non-WWW

```
www.example.com {
    redir https://example.com{uri} permanent
}
```

### Custom Headers

```
example.com {
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
    }
    reverse_proxy localhost:3000
}
```

### Handle Specific Paths Differently

```
example.com {
    handle /static/* {
        root * /var/www/static
        file_server
    }
    handle {
        reverse_proxy localhost:3000
    }
}
```

## Troubleshooting

```bash
# Check if Caddy is running
sudo systemctl status caddy

# Check for config errors
caddy validate --config /etc/caddy/Caddyfile

# Watch logs in real-time
sudo journalctl -u caddy -f

# Check what's listening on ports
sudo ss -tlnp | grep caddy
```
