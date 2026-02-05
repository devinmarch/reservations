# Cloudflare Tunnel Setup Guide

Replaced the Cloudflare Proxy setup with a Cloudflare Tunnel for better security and simpler maintenance.

## Why Tunnel Over Proxy

| | Cloudflare Proxy (old) | Cloudflare Tunnel (new) |
|---|---|---|
| Inbound ports | 80/443 open to Cloudflare IPs | None — fully closed |
| Firewall rules | ~44 rules for Cloudflare IP ranges | Just SSH for Tailscale |
| Connection | Cloudflare connects *to* your server | Server connects *out* to Cloudflare |
| Maintenance | Must update rules if Cloudflare adds IPs | None |
| TLS | Caddy handles it | Cloudflare handles visitor-facing TLS |

The tunnel creates an outbound-only connection from your server to Cloudflare. No ports need to be open for web traffic at all.

---

## Setup Steps

### 1. Install cloudflared

**On server:**
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
dpkg -i cloudflared.deb
```

Note: Use `cloudflared-linux-amd64.deb` for x86 servers.

### 2. Authenticate with Cloudflare

**On server:**
```bash
cloudflared tunnel login
```

Opens a URL — authorize in browser. Creates credentials at `~/.cloudflared/cert.pem`.

### 3. Create the Tunnel

**On server:**
```bash
cloudflared tunnel create devin-server
```

Outputs a tunnel ID (UUID) and creates credentials at `~/.cloudflared/<tunnel-id>.json`.

### 4. Create Config File

**On server:**
```bash
nano ~/.cloudflared/config.yml
```

```yaml
tunnel: aa6abeca-5714-402b-b4c4-337b51878c8b
credentials-file: /root/.cloudflared/aa6abeca-5714-402b-b4c4-337b51878c8b.json

ingress:
  - hostname: devinmarch.com
    service: http://localhost:80
  - hostname: www.devinmarch.com
    service: http://localhost:80
  - hostname: tv.devinmarch.com
    service: http://localhost:80
  - hostname: res.devinmarch.com
    service: http://localhost:80
  - service: http_status:404
```

**Important:** Use `http://localhost:80`, not `https://localhost:443`. Cloudflare handles TLS for visitors; the internal connection is plain HTTP.

Validate:
```bash
cloudflared tunnel ingress validate
```

### 5. Route DNS Through Tunnel

First, delete existing A records in Cloudflare DNS dashboard for the domains you're tunneling.

**On server:**
```bash
cloudflared tunnel route dns devin-server devinmarch.com
cloudflared tunnel route dns devin-server www.devinmarch.com
cloudflared tunnel route dns devin-server tv.devinmarch.com
cloudflared tunnel route dns devin-server res.devinmarch.com
```

This creates CNAME records pointing to `<tunnel-id>.cfargotunnel.com`.

### 6. Install as System Service

**On server:**
```bash
cloudflared service install
systemctl enable cloudflared
systemctl start cloudflared
```

The tunnel now starts automatically on boot.

### 7. Clean Up Firewall

Delete all the Cloudflare IP rules — they're no longer needed:

**On server:**
```bash
ufw status numbered
# Delete rules 2 through N (everything except SSH rule 1)
for i in $(seq 45 -1 2); do yes | ufw delete $i; done
```

Final state:
```
ufw status
```
```
Status: active

To                         Action      From
--                         ------      ----
22                         ALLOW       100.64.0.0/10
```

Only SSH over Tailscale. No web ports open at all.

---

## Caddy Configuration Change

The original Caddyfile used implicit HTTPS:

```
tv.devinmarch.com {
    reverse_proxy localhost:8096
}
```

This made Caddy:
- Listen on both HTTP and HTTPS
- Redirect HTTP to HTTPS
- Manage TLS certificates

With the tunnel, we changed to explicit HTTP:

```
http://tv.devinmarch.com {
    reverse_proxy localhost:8096
}
```

This makes Caddy:
- Listen on HTTP only (port 80)
- No redirects, no TLS
- Cloudflare handles all TLS for visitors

**Full updated Caddyfile:**
```
http://tv.devinmarch.com {
    reverse_proxy localhost:8096
}

http://devinmarch.com {
    root * /var/www/devinmarch
    file_server
}

http://www.devinmarch.com {
    redir https://devinmarch.com{uri} permanent
}

http://res.devinmarch.com, http://app.cliffsedgeretreat.ca {
    @notguest not path /r/* /ota*
    basicauth @notguest {
        devin $2a$14$...
    }

    @ota path /ota*
    basicauth @ota {
        maxxim $2a$14$...
        dev $2a$14$...
    }
    request_header @ota X-Remote-User {http.auth.user.id}

    reverse_proxy localhost:5000
}
```

Note: The `www` redirect still uses `https://` in the target URL — that's correct because it's the public-facing URL visitors should land on.

---

## Troubleshooting

### Error 1033: Cloudflare Tunnel error

The tunnel can't reach the origin. Check:

1. Is Caddy running?
   ```bash
   systemctl status caddy
   ```

2. Is Caddy responding on HTTP?
   ```bash
   curl -I http://localhost -H "Host: devinmarch.com"
   ```

3. Is the config pointing to HTTP (not HTTPS)?
   ```bash
   cat ~/.cloudflared/config.yml
   ```

### Tunnel not running after reboot

Check service status:
```bash
systemctl status cloudflared
```

If not installed as service:
```bash
cloudflared service install
systemctl enable cloudflared
systemctl start cloudflared
```

### DNS still resolving to old IP

Tailscale's DNS resolver caches aggressively. Solutions:

**On local Mac:**
```bash
sudo tailscale down
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
dig devinmarch.com +short  # should show tunnel CNAME
```

Or test with Cloudflare DNS directly:
```bash
dig @1.1.1.1 devinmarch.com +short
```

### SSL/TLS errors when using https://localhost

Caddy's automatic HTTPS doesn't work well with localhost. Use `http://localhost:80` in the tunnel config, not `https://localhost:443`.

---

## Useful Commands

**Check tunnel status:**
```bash
systemctl status cloudflared
```

**View tunnel logs:**
```bash
journalctl -u cloudflared --since "10 min ago"
```

**List tunnels:**
```bash
cloudflared tunnel list
```

**Test tunnel manually (foreground):**
```bash
cloudflared tunnel run devin-server
```

**Validate config:**
```bash
cloudflared tunnel ingress validate
```

**Test Caddy locally:**
```bash
curl -I http://localhost -H "Host: devinmarch.com"
```

---

## Traffic Flow

```
Visitor → [HTTPS] → Cloudflare → [tunnel/QUIC] → cloudflared → [HTTP] → Caddy → Flask/Jellyfin
```

- Visitor sees HTTPS (Cloudflare handles TLS)
- Tunnel uses QUIC protocol (encrypted)
- Internal connection is plain HTTP (localhost only, no exposure)

---

## Cloudflare Access Still Works

The Cloudflare Access policy on `tv.devinmarch.com` continues to work exactly as before. Traffic still goes through Cloudflare's edge, so Access gates the request before it reaches the tunnel.
