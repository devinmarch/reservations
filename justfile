# Start the server
run:
	python server.py

# Open Caddyfile
open-caddy:
	sudo nano /etc/caddy/Caddyfile

# Restart the reservations service
res-res:
	sudo systemctl restart reservations
