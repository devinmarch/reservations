from flask import Blueprint
from db import RoomStay

guest_bp = Blueprint('guest', __name__, url_prefix='/guest')


@guest_bp.route('/<reservation_id>')
def reservation(reservation_id):
    stays = list(RoomStay.select().where(RoomStay.reservation_id == reservation_id))
    if not stays:
        return "Not found", 404

    info = ""
    for s in stays:
        info += f"Room: {s.room_name}<br>Check-in: {s.room_check_in}<br>Check-out: {s.room_check_out}<br>Room Status: {s.room_status}<br>Res Status: {s.res_status}<br><br>"

    return f"<html><body>{info}</body></html>"
