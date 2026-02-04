import os
import json
import requests
from datetime import date, timedelta
from flask import Blueprint, request
from dotenv import load_dotenv

load_dotenv()

ota_bp = Blueprint('ota', __name__)

API_KEY = os.environ.get("CLOUDBEDS_API_KEY")
PROPERTY_ID = os.environ.get("CLOUDBEDS_PROPERTY_ID")

with open("ota_config.json") as f:
    USER_SOURCE_MAP = json.load(f)

@ota_bp.route('/ota')
def index():
    username = request.headers.get('X-Remote-User', '')
    user_config = USER_SOURCE_MAP.get(username, {})
    source_id = user_config.get("sourceID")
    display_name = user_config.get("displayName", username)

    if not source_id:
        return f"No sourceID configured for user: {username}", 403

    # 2 year window
    check_in_from = (date.today() - timedelta(days=30)).isoformat()
    check_in_to = (date.today() + timedelta(days=730)).isoformat()

    # Step 1: Paginate through getReservations, filter by sourceID
    matching_ids = []
    page = 1

    while True:
        resp = requests.get(
            "https://api.cloudbeds.com/api/v1.2/getReservations",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={
                "propertyID": PROPERTY_ID,
                "checkInFrom": check_in_from,
                "checkInTo": check_in_to,
                "pageNumber": page,
                "pageSize": 100
            }
        )
        data = resp.json()

        for res in data.get("data", []):
            if res.get("sourceID") == source_id:
                matching_ids.append(res["reservationID"])

        if page >= data.get("totalPages", 1):
            break
        page += 1

    if not matching_ids:
        return f"""<!DOCTYPE html>
<html><head><title>{display_name} Reservations</title>
<style>
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#333;color:white}}
</style>
</head><body>
<h1>{display_name} Reservations</h1>
<p>Found: 0 reservations</p>
<table>
<tr><th>Reservation ID</th><th>3rd Party ID</th><th>Check In</th><th>Check Out</th><th>Status</th><th>Total</th></tr>
</table>
</body></html>"""

    # Step 2: Get full details for matching reservations
    resp = requests.get(
        "https://api.cloudbeds.com/api/v1.2/getReservationsWithRateDetails",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={
            "propertyID": PROPERTY_ID,
            "reservationID": ",".join(matching_ids)
        }
    )
    details = resp.json()

    # Step 3: Build table
    rows = ""
    for res in details.get("data", []):
        rows += f"""<tr>
            <td>{res['reservationID']}</td>
            <td>{res.get('thirdPartyIdentifier', '')}</td>
            <td>{res['reservationCheckIn']}</td>
            <td>{res['reservationCheckOut']}</td>
            <td>{res['status']}</td>
            <td>${res['total']:.2f}</td>
        </tr>"""
        for room in res.get("rooms", []):
            rows += f"""<tr class="room-row">
            <td colspan="6">&nbsp;&nbsp;&nbsp;└─ {room['roomTypeName']}, {room['adults']} adults</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><title>{display_name} Reservations</title>
<style>
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#333;color:white}}
.room-row{{background:#f5f5f5;font-size:0.9em}}
</style>
</head><body>
<h1>{display_name} Reservations</h1>
<p>Found: {len(matching_ids)} reservations</p>
<table>
<tr><th>Reservation ID</th><th>3rd Party ID</th><th>Check In</th><th>Check Out</th><th>Status</th><th>Total</th></tr>
{rows}
</table>
</body></html>"""
