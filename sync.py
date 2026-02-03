import os
import requests
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from db import RoomStay

load_dotenv()

API_KEY = os.environ.get("CLOUDBEDS_API_KEY")
PROPERTY_ID = os.environ.get("CLOUDBEDS_PROPERTY_ID")
ROOM_TYPE_FILTER = "537928"

LOCKS = {
    "537928-1": {"device": "e90f7dd1-18fd-4f43-9520-dc1aaad225c6", "key": os.environ.get("SEAM_KEY_1")},
    "537928-2": {"device": "167e2aac-74d4-4049-a26d-6fb0234cc57c", "key": os.environ.get("SEAM_KEY_1")},
    "537928-3": {"device": "41be7d28-9fe1-41bb-aed8-553e993bbd26", "key": os.environ.get("SEAM_KEY_1")},
}
DAYS_BACK = (date.today() - timedelta(days=7)).isoformat()
DAYS_AHEAD = (date.today() + timedelta(days=7)).isoformat()
TZ = ZoneInfo("America/St_Johns")

# Step 1: Get reservation IDs
res_list = requests.get(
    "https://api.cloudbeds.com/api/v1.2/getReservations",
    headers={"Authorization": f"Bearer {API_KEY}"},
    params={
        "propertyID": PROPERTY_ID,
        "roomTypeID": ROOM_TYPE_FILTER,
        "checkInFrom": DAYS_BACK,
        "checkInTo": DAYS_AHEAD,
    }
).json()

res_ids = ",".join([r["reservationID"] for r in res_list["data"]]) or "null"
print(f"Found {len(res_list['data'])} reservations")

# Step 2: Get full details
response = requests.get(
    "https://api.cloudbeds.com/api/v1.2/getReservationsWithRateDetails",
    headers={"Authorization": f"Bearer {API_KEY}"},
    params={
        "propertyID": PROPERTY_ID,
        "reservationID": res_ids,
    }
)

data = response.json()
api_ids = []

for res in data["data"]:
    for room in res["rooms"]:
        room_id = room.get("roomID")
        room_name = room.get("roomName")
        stay_id = f"{res['reservationID']}_{room_id}"
        api_ids.append(stay_id)
        existing = RoomStay.get_or_none(RoomStay.id == stay_id)
        RoomStay.replace(
            id=stay_id,
            reservation_id=res["reservationID"],
            room_id=room_id,
            room_name=room_name,
            guest_name=res["guestName"],
            room_status=room["roomStatus"],
            room_check_in=room["roomCheckIn"],
            room_check_out=room["roomCheckOut"],
            res_check_in=res["reservationCheckIn"],
            res_check_out=res["reservationCheckOut"],
            res_status=res["status"],
            balance=res["balance"],
            date_modified=res["dateModified"],
            data=res,
            seam_access_code_id=existing.seam_access_code_id if existing else None
        ).execute()

print(f"Saved {len(api_ids)} room stays")

# Delete Seam access codes for records being removed
to_delete = RoomStay.select().where(
    (RoomStay.id.not_in(api_ids)) &
    (RoomStay.seam_access_code_id.is_null(False))
)

for stay in to_delete:
    lock = LOCKS.get(stay.room_id)
    if not lock:
        continue
    resp = requests.post(
        "https://connect.getseam.com/access_codes/delete",
        headers={"Authorization": f"Bearer {lock['key']}"},
        json={"access_code_id": stay.seam_access_code_id}
    )
    if resp.ok:
        print(f"Deleted Seam code for {stay.guest_name} on {stay.room_name}")
        stay.delete_instance()
    else:
        print(f"Failed to delete Seam code for {stay.guest_name}: {resp.text}")

# Delete records that never had a Seam code
deleted = RoomStay.delete().where(
    (RoomStay.id.not_in(api_ids)) &
    (RoomStay.seam_access_code_id.is_null())
).execute()
print(f"Deleted {deleted} old room stays without codes")

# Create Seam access codes for confirmed reservations
needs_code = RoomStay.select().where(
    (RoomStay.res_status == "confirmed") &
    (RoomStay.seam_access_code_id.is_null()) &
    (RoomStay.room_id.in_(list(LOCKS.keys())))
)

for stay in needs_code:
    lock = LOCKS[stay.room_id]
    pin = stay.reservation_id[-5:]
    starts_at = datetime.fromisoformat(stay.room_check_in).replace(hour=15, minute=30, tzinfo=TZ).isoformat()
    ends_at = datetime.fromisoformat(stay.room_check_out).replace(hour=11, minute=30, tzinfo=TZ).isoformat()

    # Check for existing code to adopt
    resp = requests.post("https://connect.getseam.com/access_codes/list",
        headers={"Authorization": f"Bearer {lock['key']}"}, json={"device_id": lock["device"]})
    existing = next((c for c in resp.json().get("access_codes", []) if c["code"] == pin), None)

    if existing:
        stay.seam_access_code_id = existing["access_code_id"]
        stay.save()
        print(f"Adopted existing code for {stay.guest_name} on {stay.room_name}")
        continue

    resp = requests.post(
        "https://connect.getseam.com/access_codes/create",
        headers={"Authorization": f"Bearer {lock['key']}"},
        json={
            "device_id": lock["device"],
            "code": pin,
            "name": stay.guest_name,
            "starts_at": starts_at,
            "ends_at": ends_at
        }
    )

    if resp.ok:
        code_id = resp.json()["access_code"]["access_code_id"]
        stay.seam_access_code_id = code_id
        stay.save()
        print(f"Created access code for {stay.guest_name} on {stay.room_name}")
    else:
        print(f"Failed to create code for {stay.guest_name}: {resp.text}")

# Update Seam access codes with current dates
has_code = RoomStay.select().where(RoomStay.seam_access_code_id.is_null(False))

for stay in has_code:
    lock = LOCKS.get(stay.room_id)
    if not lock:
        continue
    starts_at = datetime.fromisoformat(stay.room_check_in).replace(hour=15, minute=30, tzinfo=TZ).isoformat()
    ends_at = datetime.fromisoformat(stay.room_check_out).replace(hour=11, minute=30, tzinfo=TZ).isoformat()

    resp = requests.post(
        "https://connect.getseam.com/access_codes/update",
        headers={"Authorization": f"Bearer {lock['key']}"},
        json={
            "access_code_id": stay.seam_access_code_id,
            "starts_at": starts_at,
            "ends_at": ends_at
        }
    )
    if resp.ok:
        print(f"Updated code dates for {stay.guest_name}")
    else:
        print(f"Failed to update code for {stay.guest_name}: {resp.text}")
