# Start the server
run:
	python server.py

# Open Caddyfile
open-caddy:
	sudo nano /etc/caddy/Caddyfile

# Restart the reservations service
restart-server:
	sudo systemctl restart reservations

# View reservations server logs
logs:
	sudo journalctl -u reservations -f