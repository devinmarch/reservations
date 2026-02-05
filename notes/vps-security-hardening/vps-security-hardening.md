# VPS Security Hardening Plan

## Current Setup (Hardened)

- **Provider:** Hetzner VPS
- **Reverse Proxy:** Caddy (HTTP only, behind tunnel)
- **Remote Access:** Tailscale + SSH (firewalled to Tailscale only)
- **Web Traffic:** Cloudflare Tunnel (no inbound ports open)
- **Services:**
  - 1 static website (public via Cloudflare Tunnel)
  - Flask app via systemd (public via Cloudflare Tunnel)
  - Jellyfin media server (behind Cloudflare Access — email auth required)
- **Everything runs bare metal** (no Docker/containers)

---

## What We Implemented

### 1. SSH Firewalled to Tailscale Only (DONE)

Port 22 only accepts connections from the Tailscale subnet (100.64.0.0/10). Anyone hitting port 22 from the public internet gets nothing.

**Commands used:**
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow from 100.64.0.0/10 to any port 22
ufw enable
```

**SSH config** (`~/.ssh/config` on local machine):
```
Host hetzner
    HostName 100.125.170.128    # Tailscale IP, not public IP
    User root
```

### 2. Unattended Upgrades with Auto Reboot (DONE)

Security patches install automatically. Server reboots at 4am when kernel updates require it.

**Setup:**
```bash
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

**Config** (`/etc/apt/apt.conf.d/50unattended-upgrades`):
```
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
```

### 3. Cloudflare Tunnel for Web Traffic (DONE)

Replaced Cloudflare Proxy with Cloudflare Tunnel. No inbound ports needed for web traffic at all.

**What this gives you:**
- Server's real IP hidden
- DDoS protection
- No inbound ports open — tunnel connects *outbound* to Cloudflare
- No firewall rules to maintain for Cloudflare IPs

**Setup:**
```bash
# Install
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
dpkg -i cloudflared.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create devin-server

# Route DNS (after deleting old A records)
cloudflared tunnel route dns devin-server devinmarch.com
cloudflared tunnel route dns devin-server www.devinmarch.com
cloudflared tunnel route dns devin-server tv.devinmarch.com
cloudflared tunnel route dns devin-server res.devinmarch.com

# Install as service
cloudflared service install
systemctl enable cloudflared
systemctl start cloudflared
```

**Config file** (`~/.cloudflared/config.yml`):
```yaml
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

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

**Caddy change:** Updated Caddyfile to use `http://` prefix (e.g., `http://devinmarch.com`) since Cloudflare now handles TLS. See `cloudflare-tunnel-setup-guide.md` for details.

### 4. Cloudflare Access on Jellyfin (DONE)

`tv.devinmarch.com` is protected by Cloudflare Access. Visitors must authenticate with an approved email before they can even see the Jellyfin login page.

**Setup in Cloudflare dashboard:**
1. Access → Applications → Add application → Self-hosted
2. Application domain: `tv.devinmarch.com`
3. Create policy: Allow → Emails → (list of approved emails)

**How it works:**
- Visitor goes to `tv.devinmarch.com`
- Cloudflare shows email login page
- They enter email, receive one-time pin
- If email is on the allowed list, they get through to Jellyfin
- If not, blocked

---

## Current Firewall State

```
ufw status
```

| Port | Exposed To |
|------|------------|
| 22 | Tailscale subnet only (100.64.0.0/10) |

That's it. No web ports open at all. The tunnel handles everything via outbound connections.

---

## Known Gotcha: Tailscale DNS Caching

Tailscale runs its own DNS resolver (`100.100.100.100`) which caches DNS records. After moving DNS to Cloudflare, Tailscale may continue resolving your domains to the old server IP instead of Cloudflare's IP.

**Symptoms:**
- Sites timeout when connected to Tailscale
- Sites work when disconnected from Tailscale
- `dig devinmarch.com +short` returns your server IP instead of Cloudflare's

**Solutions:**
1. **Wait** — the cache clears eventually (usually within an hour)
2. **Disconnect from Tailscale** when you need to access your sites
3. **Restart Tailscale** — `sudo tailscale down && sudo tailscale up`
4. **Test with Cloudflare DNS directly** — `dig @1.1.1.1 devinmarch.com +short`

This only affects your local machine. Other users without Tailscale won't have this issue.

---

## Useful Commands

**Check firewall status:**
```bash
ufw status
ufw status numbered    # with rule numbers for deletion
```

**Check what's being blocked:**
```bash
tail -50 /var/log/ufw.log
```

**Check if Caddy is running:**
```bash
systemctl status caddy
```

**Test DNS resolution:**
```bash
dig devinmarch.com +short           # uses your default DNS
dig @1.1.1.1 devinmarch.com +short  # uses Cloudflare's DNS directly
```

**Flush local DNS cache (Mac):**
```bash
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```

---

## Future Considerations

- **Switch from root to non-root user** — Create a user with sudo, disable root login
- **Cloudflare Access for Flask app** — If you want email auth on `res.devinmarch.com` too, same process as Jellyfin
