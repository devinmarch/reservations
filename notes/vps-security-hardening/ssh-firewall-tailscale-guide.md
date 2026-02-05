# SSH + Firewall + Tailscale Guide

How we locked down SSH on the Hetzner VPS so it's only accessible over Tailscale.

## What We Did

1. Updated local SSH config to use the server's Tailscale IP instead of the public IP
2. Installed and configured `ufw` to block all inbound traffic except what we explicitly allow
3. Restricted SSH (port 22) to the Tailscale subnet only
4. Left ports 80/443 open for web traffic (Caddy)

## The SSH Config Change

**Before** — SSH over public internet:
```
Host hetzner
    HostName 77.42.29.91
    User root
```

**After** — SSH over Tailscale:
```
Host hetzner
    HostName 100.125.170.128
    User root
```

To find your server's Tailscale IP:
```
tailscale ip -4
```

## UFW Firewall Setup

### Install
```
apt update && apt install ufw
```

### Configure Rules
```
# Block everything inbound by default, allow outbound
ufw default deny incoming
ufw default allow outgoing

# Allow SSH only from Tailscale subnet
ufw allow from 100.64.0.0/10 to any port 22

# Allow web traffic from anywhere
ufw allow 80
ufw allow 443

# Turn it on
ufw enable
```

### Verify
```
ufw status verbose
```

Should show:
```
To                         Action      From
--                         ------      ----
22                         ALLOW IN    100.64.0.0/10
80                         ALLOW IN    Anywhere
443                        ALLOW IN    Anywhere
80 (v6)                    ALLOW IN    Anywhere (v6)
443 (v6)                   ALLOW IN    Anywhere (v6)
```

### Useful UFW Commands
```
ufw status              # check current rules
ufw status numbered     # show rules with numbers (useful for deleting)
ufw delete 3            # delete rule number 3
ufw allow from 100.64.0.0/10 to any port 8096   # example: open Jellyfin to Tailscale
ufw disable             # turn off firewall
ufw reset               # wipe all rules and start over
```

## Why 100.64.0.0/10?

This is the full Tailscale address range. All Tailscale IPs fall within `100.64.0.0` to `100.127.255.255`. Using `/10` covers the entire range so any device on your Tailscale network can reach SSH.

## Testing

Confirm the public IP is blocked:
```
ssh root@77.42.29.91
```
This should hang and timeout.

Confirm Tailscale still works:
```
ssh hetzner
```
This should connect immediately.

## Safety Notes

- Always update your SSH config to use Tailscale **before** enabling firewall rules. Otherwise you can lock yourself out.
- Hetzner has a web console in their dashboard as a last resort if you lose access.
- Tailscale must be running on both your local machine and the server for SSH to work.

---

## Next Step: Stop Using Root

Right now we're logging in as `root`. Best practice is to create a normal user with sudo access and disable root login. This limits the damage if an account is compromised — root can do anything, a sudo user at least requires an extra password step.

### Create a User
```
adduser devin
usermod -aG sudo devin
```

### Copy Your SSH Key to the New User
```
mkdir -p /home/devin/.ssh
cp /root/.ssh/authorized_keys /home/devin/.ssh/authorized_keys
chown -R devin:devin /home/devin/.ssh
chmod 700 /home/devin/.ssh
chmod 600 /home/devin/.ssh/authorized_keys
```

### Update Local SSH Config
```
Host hetzner
    HostName 100.125.170.128
    User devin
```

### Disable Root Login
Edit `/etc/ssh/sshd_config` on the server:
```
PermitRootLogin no
```

Then restart SSH:
```
systemctl restart sshd
```

**Important:** Test that you can `ssh hetzner` with the new user before disabling root. Don't lock yourself out.
