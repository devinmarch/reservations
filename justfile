# Start the server
run:
	python server.py

# Restart the reservations service
restart:
	sudo systemctl restart reservations

# View reservations server logs
logs:
	sudo journalctl -u reservations -f

# Activate virtual environment
venv:
	source venv/bin/activate