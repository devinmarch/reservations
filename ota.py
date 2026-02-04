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
    source_id = USER_SOURCE_MAP.get(username)

    if not source_id:
        return f"No sourceID configured for user: {username}", 403

    # 2 year window
    check_in_from = (date.today() - timedelta(days=365)).isoformat()
    check_in_to = (date.today() + timedelta(days=365)).isoformat()

    # Step 1: Paginate through getReservations, filter by sourceID
    matching_ids = []
    all_source_ids = set()
    total_checked = 0
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
            total_checked += 1
            res_source_id = res.get("source", {}).get("sourceID")
            if res_source_id:
                all_source_ids.add(res_source_id)
            if res_source_id == source_id:
                matching_ids.append(res["reservationID"])

        if page >= data.get("totalPages", 1):
            break
        page += 1

    if not matching_ids:
        debug = f"<p>Checked {total_checked} reservations across {page} pages</p>"
        debug += f"<p>Looking for: <code>{source_id}</code></p>"
        debug += f"<p>Found sourceIDs: <code>{sorted(all_source_ids)}</code></p>"
        return f"<html><body><h1>OTA Reservations</h1><p>No reservations found</p>{debug}</body></html>"

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
            <td>${res['total']:.2f}</td>
        </tr>"""
        for room in res.get("rooms", []):
            rows += f"""<tr class="room-row">
            <td colspan="5">&nbsp;&nbsp;&nbsp;└─ {room['roomTypeName']}, {room['adults']} adults</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><title>OTA Reservations</title>
<style>
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#333;color:white}}
.room-row{{background:#f5f5f5;font-size:0.9em}}
</style>
</head><body>
<h1>OTA Reservations</h1>
<p>Source: {source_id} | Found: {len(matching_ids)} reservations</p>
<table>
<tr><th>Reservation ID</th><th>3rd Party ID</th><th>Check In</th><th>Check Out</th><th>Total</th></tr>
{rows}
</table>
</body></html>"""
