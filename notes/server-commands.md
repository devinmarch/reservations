# Server Commands Reference

## Services

The reservations app runs as a systemd service:

- **Service name**: `reservations.service`
- **Service file**: `/etc/systemd/system/reservations.service`

## Watching Logs

```bash
# Reservations app logs (live)
sudo journalctl -u reservations -f

# Caddy logs (live)
sudo journalctl -u caddy -f

# With recent history
sudo journalctl -u reservations -f --since "5 minutes ago"
```

## Caddy Config

```bash
# Copy updated Caddyfile and reload
sudo cp config/Caddyfile /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

- `reload` = zero downtime, re-reads config
- `restart` = full stop/start, brief interruption

## Useful Commands

```bash
# List all services
systemctl list-units --type=service

# Check custom services
ls /etc/systemd/system/*.service

# Service control
sudo systemctl status reservations
sudo systemctl restart reservations
sudo systemctl stop reservations
sudo systemctl start reservations

# See running Python processes
ps aux | grep python
```
