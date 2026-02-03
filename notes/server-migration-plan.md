# Server Migration Plan: Coolify → Bare Metal

## Phase 1: Install Jellyfin bare metal

```bash
# Add Jellyfin repo (Debian/Ubuntu)
curl https://repo.jellyfin.org/install-debuntu.sh | bash
```

Then edit the config to use your existing data:

```bash
sudo nano /etc/jellyfin/jellyfin.service.d/override.conf
```

We'll configure it to point at `/opt/jellyfin/config`, `/opt/jellyfin/cache`, and `/media`.

---

## Phase 2: Stop Docker Jellyfin, verify bare metal works

```bash
# Stop Docker Jellyfin
docker stop jellyfin

# Start bare metal Jellyfin
sudo systemctl start jellyfin

# Check it's running
sudo systemctl status jellyfin
curl localhost:8096
```

If something's wrong, you can revert: `docker start jellyfin`

---

## Phase 3: Remove Coolify and Docker

```bash
# Stop all remaining containers
docker stop $(docker ps -q)

# Remove Coolify containers
docker rm coolify coolify-db coolify-redis coolify-proxy coolify-sentinel coolify-realtime

# Remove your website container
docker rm r8sk4ssogscw004osoc4k0cs-030246461651

# Remove the old Jellyfin container
docker rm jellyfin

# Remove all Docker volumes
docker volume prune -f

# Remove Coolify data directory
rm -rf /data/coolify

# Clean up Docker images/networks
docker system prune -a -f

# Optionally: remove Docker entirely
# apt remove docker-ce docker-ce-cli containerd.io
```

---

## Phase 4: Install and configure Caddy

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Edit Caddyfile
sudo nano /etc/caddy/Caddyfile
```

Caddyfile content:
```
jellyfin.yourdomain.com {
    reverse_proxy localhost:8096
}

yourdomain.com {
    root * /var/www/yoursite
    file_server
}
```

```bash
# Start Caddy
sudo systemctl enable caddy
sudo systemctl start caddy
```

---

## Phase 5: Deploy static website

```bash
# Clone from GitHub
sudo mkdir -p /var/www
cd /var/www
sudo git clone https://github.com/yourusername/yoursite.git yoursite

# Set permissions
sudo chown -R caddy:caddy /var/www/yoursite
```

Site should now be live.

---

## Phase 6: Deploy Flask reservation app

```bash
# Clone the repo
cd /var/www
sudo git clone git@github.com:devinmarch/reservations.git reservations

# Install Python dependencies
cd reservations
sudo apt install python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # or pip install flask seam sqlite3 etc.

# Create systemd service
sudo nano /etc/systemd/system/reservations.service
```

Service file content:
```ini
[Unit]
Description=Reservations Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/reservations
Environment="PATH=/var/www/reservations/venv/bin"
ExecStart=/var/www/reservations/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start the service
sudo systemctl enable reservations
sudo systemctl start reservations
```

### Environment variables

Use `.env` files for different environments (API keys, database paths, etc.).

```bash
# Create .env on server
nano /var/www/reservations/.env
```

Add your production values:
```
SEAM_API_KEY=your_production_key
DATABASE_PATH=/var/www/reservations/reservations.db
```

Locally, you have a different `.env` with local/test values.

```bash
# Make sure .env is gitignored
echo ".env" >> .gitignore
```

Your Python code loads it with:
```python
from dotenv import load_dotenv
load_dotenv()  # reads .env file
api_key = os.environ.get('SEAM_API_KEY')
```

This way the same code runs everywhere - it just reads whatever `.env` is present.

```bash
# Add to Caddyfile
sudo nano /etc/caddy/Caddyfile
```

Add to Caddyfile:
```
reservations.devinmarch.com {
    reverse_proxy localhost:5000
}
```

```bash
sudo systemctl reload caddy
```

---

## Phase 7: VSCode Remote SSH + GitHub workflow

### Setup SSH access from VSCode

1. Install "Remote - SSH" extension in VSCode
2. Open Command Palette → "Remote-SSH: Connect to Host"
3. Enter: `root@77.42.29.91` (or add to ~/.ssh/config)

### Working directly on server

When connected via Remote SSH, you're editing files on the server directly. Changes are live immediately (after restarting the Flask service if needed).

```bash
# After making changes on server
cd /var/www/reservations
git add .
git commit -m "your message"
git push origin main
```

### Working locally then deploying

```bash
# Local machine - make changes, commit, push
git add .
git commit -m "your message"
git push origin main

# Then SSH to server and pull
ssh root@77.42.29.91
cd /var/www/reservations
git pull origin main
sudo systemctl restart reservations
```

### Key concept

- **Local dev**: Edit → test locally → commit → push → SSH to server → pull → restart service
- **Remote dev (VSCode SSH)**: Edit on server → test live → commit → push (no pull needed, you're already there)

Both workflows push to the same GitHub repo as the source of truth.

---

## Completed phases

- [x] Phase 1: Install Jellyfin bare metal
- [x] Phase 2: Stop Docker Jellyfin, verify bare metal works
- [x] Phase 3: Remove Coolify and Docker
- [x] Phase 4: Install and configure Caddy
- [x] Phase 5: Deploy static website
- [ ] Phase 6: Deploy Flask reservation app
- [ ] Phase 7: VSCode Remote SSH + GitHub workflow
