# Unattended Upgrades Guide

Automatically install security patches on the server so you don't have to manually run `apt upgrade`.

## What It Does

- Checks for security updates daily
- Installs them automatically
- Reboots the server when a kernel update requires it (at a time you choose)
- Only handles **security updates** — it won't upgrade major versions of packages (Python, Caddy, etc.) and break things

## Setup

### Install
```
apt install unattended-upgrades
```
Was already installed on our Hetzner image.

### Enable
```
dpkg-reconfigure -plow unattended-upgrades
```
Select "Yes" when prompted.

### Configure Auto-Reboot

Edit `/etc/apt/apt.conf.d/50unattended-upgrades` and uncomment/set these two lines:

```
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
```

- `Automatic-Reboot "true"` — allows the server to reboot itself when a kernel update requires it
- `Automatic-Reboot-Time "04:00"` — reboots at 4am to minimize disruption

Without these, kernel updates get installed but don't take effect until you manually reboot.

## Verify It's Running

```
systemctl status unattended-upgrades
```

Check logs:
```
cat /var/log/unattended-upgrades/unattended-upgrades.log
```

## Notes

- Services managed by systemd (Caddy, Flask app, Jellyfin) will come back up automatically after a reboot
- Reboots only happen when necessary (kernel updates), not on every patch
- The 13 pending updates from `apt install` output can be applied manually with `apt upgrade` whenever you want — those may include non-security updates that unattended-upgrades intentionally skips
