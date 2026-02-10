import json
from datetime import date, timedelta
from flask import Blueprint, request, render_template, jsonify
from .api import (
    get_reservations, get_reservations_with_details, get_rate_plans,
    post_reservation, post_adjustment, post_note, put_note, get_notes
)

ota_bp = Blueprint('ota', __name__, template_folder='templates', static_folder='static', static_url_path='/ota/static')

with open("ota_config.json") as f:
    CONFIG = json.load(f)


def get_username():
    """Get username from header, with query param fallback for local dev."""
    return request.headers.get('X-Remote-User', '') or request.args.get('_user', '')


@ota_bp.route('/ota')
def index():
    username = get_username()
    user_config = CONFIG.get("users", {}).get(username, {})
    source_id = user_config.get("sourceID")
    display_name = user_config.get("displayName", username)

    if not source_id:
        return f"No sourceID configured for user: {username}", 403

    room_types = CONFIG.get("roomTypes", {})
    return render_template('list.html', display_name=display_name, room_types=room_types)


@ota_bp.route('/ota/api/reservations')
def api_reservations():
    username = get_username()
    user_config = CONFIG.get("users", {}).get(username, {})
    source_id = user_config.get("sourceID")

    if not source_id:
        return jsonify({"error": "No sourceID configured"}), 403

    check_in_from = (date.today() - timedelta(days=30)).isoformat()
    check_in_to = (date.today() + timedelta(days=730)).isoformat()

    matching_ids = []
    page = 1
    while True:
        data = get_reservations(check_in_from, check_in_to, page)
        for res in data.get("data", []):
            if res.get("sourceID") == source_id:
                matching_ids.append(res["reservationID"])
        if len(data.get("data", [])) < 100:
            break
        page += 1

    if not matching_ids:
        return jsonify([])

    details = get_reservations_with_details(matching_ids)
    return jsonify(details.get("data", []))


@ota_bp.route('/ota/availability', methods=['POST'])
def check_availability():
    username = get_username()
    user_config = CONFIG.get("users", {}).get(username, {})

    if not user_config:
        return jsonify({"error": "User not configured"}), 403

    data = request.get_json()
    check_in = data.get("checkIn")
    check_out = data.get("checkOut")

    if not check_in or not check_out:
        return jsonify({"error": "checkIn and checkOut required"}), 400

    # Get user's allowed rooms (keys of otaRates)
    user_rooms = set(user_config.get("otaRates", {}).keys())
    room_types = CONFIG.get("roomTypes", {})

    # Build rateID -> roomTypeID mapping for rooms user can book
    rate_to_room = {}
    for room_id in user_rooms:
        if room_id in room_types:
            rate_id = room_types[room_id].get("rateID")
            if rate_id:
                rate_to_room[rate_id] = room_id

    # Fetch availability from CloudBeds
    result = get_rate_plans(check_in, check_out)

    # Map results to roomTypeID -> roomsAvailable
    availability = {}
    for rate in result.get("data", []):
        rate_id = str(rate.get("rateID"))
        if rate_id in rate_to_room:
            room_id = rate_to_room[rate_id]
            availability[room_id] = rate.get("roomsAvailable", 0)

    return jsonify({"availability": availability})


@ota_bp.route('/ota/create', methods=['POST'])
def create_reservation():
    username = get_username()
    user_config = CONFIG.get("users", {}).get(username, {})

    if not user_config:
        return jsonify({"error": "User not configured"}), 403

    data = request.get_json()
    check_in = data.get("checkIn")
    check_out = data.get("checkOut")
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    ota_ref = data.get("otaRef", "")
    notes = data.get("notes", "")
    rooms = data.get("rooms", [])

    if not all([check_in, check_out, first_name, last_name, rooms]):
        return jsonify({"error": "Missing required fields"}), 400

    # Re-check availability
    room_types = CONFIG.get("roomTypes", {})
    user_rooms = set(user_config.get("otaRates", {}).keys())

    rate_to_room = {}
    for room_id in user_rooms:
        if room_id in room_types:
            rate_id = room_types[room_id].get("rateID")
            if rate_id:
                rate_to_room[rate_id] = room_id

    result = get_rate_plans(check_in, check_out)

    availability = {}
    for rate in result.get("data", []):
        rate_id = str(rate.get("rateID"))
        if rate_id in rate_to_room:
            room_id = rate_to_room[rate_id]
            availability[room_id] = rate.get("roomsAvailable", 0)

    # Count requested rooms per type
    requested = {}
    for room in rooms:
        room_id = room.get("roomTypeId")
        requested[room_id] = requested.get(room_id, 0) + 1

    # Verify availability
    for room_id, count in requested.items():
        if room_id not in availability:
            return jsonify({"error": f"Room type {room_id} not available"}), 400
        if count > availability[room_id]:
            return jsonify({"error": f"Not enough rooms available for {room_types.get(room_id, {}).get('name', room_id)}"}), 400

    # Build payload with bracket notation
    defaults = CONFIG.get("defaults", {})
    payload = {
        "propertyID": result.get("propertyID", ""),
        "sourceID": user_config.get("sourceID"),
        "thirdPartyIdentifier": ota_ref,
        "startDate": check_in,
        "endDate": check_out,
        "guestFirstName": first_name,
        "guestLastName": last_name,
        "guestEmail": user_config.get("email", ""),
        "guestPhone": user_config.get("phone", ""),
        "guestCountry": defaults.get("country", "CA"),
        "paymentMethod": defaults.get("paymentMethod", "cash"),
    }

    for i, room in enumerate(rooms):
        room_id = room.get("roomTypeId")
        guests = room.get("guests", 1)
        payload[f"rooms[{i}][roomTypeID]"] = room_id
        payload[f"rooms[{i}][quantity]"] = 1
        payload[f"adults[{i}][roomTypeID]"] = room_id
        payload[f"adults[{i}][quantity]"] = guests
        payload[f"children[{i}][roomTypeID]"] = room_id
        payload[f"children[{i}][quantity]"] = 0

    # Create reservation
    res_result = post_reservation(payload)

    if not res_result.get("success"):
        return jsonify({"error": res_result.get("message", "Failed to create reservation")}), 400

    reservation_id = res_result.get("reservationID")
    grand_total = float(res_result.get("grandTotal", 0))

    # Calculate and post adjustment
    tax_rate = defaults.get("taxRate", 0.15)
    adjustment_percent = user_config.get("adjustmentPercent", 0)
    adjustment_amount = grand_total / (1 + tax_rate) * adjustment_percent

    if adjustment_amount != 0:
        adj_result = post_adjustment(
            reservation_id,
            round(adjustment_amount, 2),
            f"{user_config.get('displayName', username)} commission adjustment"
        )
        if not adj_result.get("success"):
            return jsonify({"error": "Reservation created but adjustment failed"}), 500

    # Post note if provided
    if notes.strip():
        note_result = post_note(reservation_id, notes)
        if not note_result.get("success"):
            return jsonify({"error": "Reservation created but note failed"}), 500

    return jsonify({"success": True, "reservationID": reservation_id})


@ota_bp.route('/ota/api/notes/<reservation_id>')
def api_notes(reservation_id):
    result = get_notes(reservation_id)
    return jsonify(result.get("data", []))


@ota_bp.route('/ota/api/notes/<reservation_id>', methods=['POST'])
def api_post_note(reservation_id):
    data = request.get_json()
    result = post_note(reservation_id, data.get("note", ""))
    return jsonify(result)


@ota_bp.route('/ota/api/notes/<reservation_id>/<note_id>', methods=['PUT'])
def api_put_note(reservation_id, note_id):
    data = request.get_json()
    result = put_note(reservation_id, note_id, data.get("note", ""))
    return jsonify(result)
