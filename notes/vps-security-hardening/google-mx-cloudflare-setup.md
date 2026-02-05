# Google Workspace DNS Records on Cloudflare

All records below should be **DNS only** (grey cloud) — never proxied.

---

## MX Record (Routes Incoming Mail to Gmail)

| Type | Name | Value | Priority |
|------|------|-------|----------|
| MX | `@` | `smtp.google.com` | 1 |

This is the modern single-record setup (post-April 2023). Replaces the legacy 5-record configuration. Both work, but Google recommends this for new setups.

---

## SPF (Prevents Spoofing of Outbound Mail)

| Type | Name | Value |
|------|------|-------|
| TXT | `@` | `v=spf1 include:_spf.google.com ~all` |

- Only **one** SPF record per domain. If other services also send mail, merge them into one record (e.g. `v=spf1 include:_spf.google.com include:othersender.com ~all`).
- `~all` = soft fail (recommended to start). `-all` = hard fail (stricter, use once confident).

---

## DKIM (Cryptographically Signs Outgoing Mail)

Generated in Google Admin Console:

1. **Admin Console** → Apps → Google Workspace → Gmail → **Authenticate email**
2. Generate a **2048-bit** DKIM key
3. Google gives you a TXT record to add:

| Type | Name | Value |
|------|------|-------|
| TXT | `google._domainkey` | `v=DKIM1; k=rsa; p=<long public key string>` |

4. After adding in Cloudflare, go back to Admin Console and click **Start authentication**

---

## DMARC (Tells Receivers What to Do with Unauthenticated Mail)

| Type | Name | Value |
|------|------|-------|
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.com` |

- Start with `p=none` to monitor without blocking anything.
- Tighten to `p=quarantine` or `p=reject` once SPF and DKIM are confirmed working and you've reviewed reports.

---

## Optional Records

- **Domain verification TXT** — One-time TXT record at `@` provided by Google during Workspace signup.
- **Custom service URLs** — CNAME records like `mail.yourdomain.com` → `ghs.googlehosted.com` if you want friendly URLs for Gmail, Calendar, etc.

---

## Cloudflare Tips

- Set **TTL to Auto** (or 300s) during setup for faster propagation.
- Allow up to **48 hours** for full propagation.
- Test with [MX Toolbox](https://mxtoolbox.com), [mail-tester.com](https://mail-tester.com), or Google Postmaster Tools.
