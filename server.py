from flask import Flask, redirect
import subprocess
import sys
from db import RoomStay
from ota import ota_bp
from guest import guest_bp

app = Flask(__name__)
app.register_blueprint(ota_bp)
app.register_blueprint(guest_bp)

@app.route("/sync")
def sync():
    subprocess.run([sys.executable, "sync.py"])
    return redirect("/")

@app.route("/")
def index():
    rows = ""
    for r in RoomStay.select():
        rows += f"<tr><td>{r.id}</td><td>{r.reservation_id}</td><td>{r.room_id}</td><td>{r.room_name}</td><td>{r.guest_name}</td><td>{r.room_status}</td><td>{r.room_check_in}</td><td>{r.room_check_out}</td><td>{r.res_check_in}</td><td>{r.res_check_out}</td><td>{r.res_status}</td><td>${r.balance:.2f}</td><td>{r.date_modified}</td><td>{r.seam_access_code_id or ''}</td></tr>"

    return f"""<!DOCTYPE html>
<html><head><title>Room Stays</title>
<style>table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px}}th{{background:#333;color:white}}</style>
</head><body><h1>Room Stays</h1>
<a href="/sync"><button>Sync Now</button></a>
<table><tr><th>ID</th><th>Res ID</th><th>Room ID</th><th>Room</th><th>Guest</th><th>Room Status</th><th>Room In</th><th>Room Out</th><th>Res In</th><th>Res Out</th><th>Res Status</th><th>Balance</th><th>Modified</th><th>Seam Code</th></tr>{rows}</table>
</body></html>"""

if __name__ == "__main__":
    app.run(debug=True)
