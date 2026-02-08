from flask import Blueprint, render_template, request, jsonify
from db import RoomStay, ChatMessage

guest_bp = Blueprint('guest', __name__, template_folder='templates', static_folder='static', url_prefix='/guest')


def get_stays_or_404(reservation_id):
    stays = list(RoomStay.select().where(RoomStay.reservation_id == reservation_id))
    return stays if stays else None


@guest_bp.route('/<reservation_id>')
def reservation(reservation_id):
    stays = get_stays_or_404(reservation_id)
    if not stays:
        return "Not found", 404
    return render_template('booking.html', reservation_id=reservation_id, stays=stays, page='booking')


@guest_bp.route('/<reservation_id>/chat')
def chat(reservation_id):
    if not get_stays_or_404(reservation_id):
        return "Not found", 404
    return render_template('chat.html', reservation_id=reservation_id, page='messages')


@guest_bp.route('/<reservation_id>/activities')
def activities(reservation_id):
    if not get_stays_or_404(reservation_id):
        return "Not found", 404
    return render_template('activities.html', reservation_id=reservation_id, page='activities')


@guest_bp.route('/<reservation_id>/food')
def food(reservation_id):
    if not get_stays_or_404(reservation_id):
        return "Not found", 404
    return render_template('food.html', reservation_id=reservation_id, page='food')


@guest_bp.route('/<reservation_id>/food/reserve')
def food_reserve(reservation_id):
    if not get_stays_or_404(reservation_id):
        return "Not found", 404
    return render_template('food_reserve.html', reservation_id=reservation_id, page='food',
                           title='Book a Table', back_url=f'/guest/{reservation_id}/food')


@guest_bp.route('/<reservation_id>/profile')
def profile(reservation_id):
    if not get_stays_or_404(reservation_id):
        return "Not found", 404
    return render_template('profile.html', reservation_id=reservation_id, page='profile')


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
