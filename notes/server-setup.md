### Add setting to make sure print() logs aren't buffered
sudo sed -i '/WorkingDirectory/a Environment=PYTHONUNBUFFERED=1' /etc/systemd/system/reservations.service
sudo systemctl daemon-reload
sudo systemctl restart reservations
