from flask import Blueprint, render_template, request, jsonify
from db import RoomStay
from chat_db import ChatMessage

guest_bp = Blueprint('guest', __name__, template_folder='templates', url_prefix='/guest')


@guest_bp.route('/<reservation_id>')
def reservation(reservation_id):
    stays = list(RoomStay.select().where(RoomStay.reservation_id == reservation_id))
    if not stays:
        return "Not found", 404

    info = ""
    for s in stays:
        info += f"Room: {s.room_name}<br>Check-in: {s.room_check_in}<br>Check-out: {s.room_check_out}<br>Room Status: {s.room_status}<br>Res Status: {s.res_status}<br><br>"

    return f"<html><body>{info}</body></html>"


@guest_bp.route('/<reservation_id>/chat')
def chat(reservation_id):
    stays = list(RoomStay.select().where(RoomStay.reservation_id == reservation_id))
    if not stays:
        return "Not found", 404
    return render_template('chat.html', reservation_id=reservation_id)


@guest_bp.route('/<reservation_id>/messages')
def messages(reservation_id):
    msgs = list(
        ChatMessage.select()
        .where(ChatMessage.reservation_id == reservation_id)
        .order_by(ChatMessage.created_at)
    )
    return jsonify([
        {"sender": m.sender, "message": m.message, "created_at": str(m.created_at)}
        for m in msgs
    ])


@guest_bp.route('/<reservation_id>/messages', methods=['POST'])
def post_message(reservation_id):
    data = request.get_json()
    ChatMessage.create(
        reservation_id=reservation_id,
        sender="guest",
        message=data.get("message", "").strip()
    )
    return jsonify({"success": True})
