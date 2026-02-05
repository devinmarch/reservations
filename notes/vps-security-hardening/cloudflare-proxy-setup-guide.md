# Cloudflare Proxy Setup Guide

How we put Cloudflare in front of our web services so ports 80/443 are no longer open to the entire internet.

## What This Does

Before:
```
Visitor → Your Server (77.42.29.91:443)
```

After:
```
Visitor → Cloudflare → Your Server (77.42.29.91:443)
```

- Hides your server's real IP — DNS resolves to Cloudflare, not your server
- DDoS protection — Cloudflare absorbs junk traffic before it reaches you
- Firewall lockdown — only Cloudflare's IP ranges can reach ports 80/443

## Steps We Followed

### 1. Create Cloudflare Account

- Sign up at cloudflare.com (free plan is sufficient)
- Add your domain (e.g., `devinmarch.com`)
- Cloudflare scans and imports existing DNS records

### 2. Verify DNS Records

Cloudflare's scan may miss records. Compare what it imported against your existing DNS provider (Namecheap, etc.).

**Records we needed for devinmarch.com:**

| Type | Name | Content | Proxy Status |
|------|------|---------|-------------|
| A | devinmarch.com | 77.42.29.91 | Proxied (orange cloud) |
| A | tv | 77.42.29.91 | Proxied (orange cloud) |
| A | www | 77.42.29.91 | Proxied (orange cloud) |
| A | res | 77.42.29.91 | Proxied (orange cloud) |
| CNAME | gallery | domain.pixieset.com | DNS only (gray cloud) |
| MX | devinmarch.com | (5 Gmail MX records) | DNS only |
| TXT | devinmarch.com | SPF, DKIM, DMARC for Gmail | DNS only |

**Important:**
- A records pointing to your server should be **Proxied** (orange cloud) — this routes traffic through Cloudflare
- CNAME records for third-party services (like Pixieset) should be **DNS only** (gray cloud) — proxying can break external services
- MX and TXT records are always DNS only

### 3. Update Nameservers

At your domain registrar (Namecheap), change nameservers to the ones Cloudflare provides (e.g., `ariella.ns.cloudflare.com`).

- Domain registration stays at Namecheap, only DNS management moves to Cloudflare
- Propagation can take minutes to 48 hours
- **All DNS records must be in Cloudflare before switching** — anything missing will break

### 4. Verify Propagation

Check in terminal:
```
dig devinmarch.com NS +short
```
Should return Cloudflare nameservers.

Cloudflare dashboard Overview page will show "Your domain is now protected by Cloudflare" when active.

### 5. Set SSL/TLS Mode

In Cloudflare dashboard → SSL/TLS → set to **Full (Strict)**.

- **Full (Strict)** — Cloudflare encrypts to origin and verifies Caddy's certificate is valid (correct setting)
- **Full** — encrypts but doesn't verify the certificate
- **Flexible** — Cloudflare talks to Caddy over plain HTTP (don't use this)

### 6. Firewall Ports 80/443 to Cloudflare Only

First, delete the old open rules:
```
ufw status numbered
# Delete the "Anywhere" rules for 80 and 443 (highest number first)
ufw delete 5
ufw delete 4
ufw delete 3
ufw delete 2
```

Then add Cloudflare's IP ranges (fetched from cloudflare.com/ips-v4 and cloudflare.com/ips-v6):

```
# IPv4 ranges
for ip in 173.245.48.0/20 103.21.244.0/22 103.22.200.0/22 103.31.4.0/22 141.101.64.0/18 108.162.192.0/18 190.93.240.0/20 188.114.96.0/20 197.234.240.0/22 198.41.128.0/17 162.158.0.0/15 104.16.0.0/13 104.24.0.0/14 172.64.0.0/13 131.0.72.0/22; do
  ufw allow from $ip to any port 80
  ufw allow from $ip to any port 443
done

# IPv6 ranges
for ip in 2400:cb00::/32 2606:4700::/32 2803:f800::/32 2405:b500::/32 2405:8100::/32 2a06:98c0::/29 2c0f:f248::/32; do
  ufw allow from $ip to any port 80
  ufw allow from $ip to any port 443
done
```

### 7. Verify

- Sites load via domain names (traffic goes through Cloudflare)
- `https://77.42.29.91` directly times out (server is not reachable outside Cloudflare)

## Troubleshooting

### Sites not loading after DNS switch
- Flush local DNS cache: `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`
- Try from a different device/network (phone on cellular)
- DNS propagation can take time — old DNS may be cached locally

### Check if DNS is resolving to Cloudflare
```
dig res.devinmarch.com +short
```
Should return Cloudflare IPs (e.g., `172.67.x.x`, `104.21.x.x`), NOT your server IP.

### Check if Caddy is running
```
systemctl status caddy
curl -I http://localhost
```

### Check firewall logs for blocked connections
```
tail -50 /var/log/ufw.log
```
Look for `[UFW BLOCK]` entries on ports 80/443. Cloudflare IPs being blocked means the firewall rules are wrong.

## How Caddy and Cloudflare Work Together

Caddy still does everything it did before — terminates TLS, reverse proxies to your services, handles routing. The only difference is all traffic now comes from Cloudflare's IP ranges instead of random visitors.

```
Visitor → [TLS] → Cloudflare → [TLS] → Caddy → Flask/Jellyfin/static site
```

Two layers of TLS. Cloudflare decrypts, then re-encrypts to talk to Caddy. This is normal with Full (Strict) mode.

## Note on Cloudflare IP Ranges

Cloudflare occasionally adds new IP ranges. If they do and you don't update your firewall rules, traffic from those new IPs would be blocked. This is rare but worth checking once or twice a year at cloudflare.com/ips.
