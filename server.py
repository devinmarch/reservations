import os
from flask import Flask
from db import db, RoomStay, ChatMessage
from devices import Lock
from reservations.common_sync import CommonCode
from reservations import reservations_bp
from ota import ota_bp
from guest import guest_bp
from staff import staff_bp
from room_block import room_block_bp, RoomBlockCode

app = Flask(__name__)
app.register_blueprint(reservations_bp)
app.register_blueprint(ota_bp)
app.register_blueprint(guest_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(room_block_bp)

db.create_tables([RoomStay, ChatMessage, Lock, CommonCode, RoomBlockCode])

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
    app.run(debug=os.environ.get("FLASK_DEBUG", False))
