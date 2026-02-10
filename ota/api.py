import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("CLOUDBEDS_API_KEY")
PROPERTY_ID = os.environ.get("CLOUDBEDS_PROPERTY_ID")
BASE_URL = "https://api.cloudbeds.com/api/v1.2"


def get_reservations(check_in_from, check_in_to, page=1, page_size=100):
    """Fetch a page of reservations."""
    resp = requests.get(
        f"{BASE_URL}/getReservations",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={
            "propertyID": PROPERTY_ID,
            "checkInFrom": check_in_from,
            "checkInTo": check_in_to,
            "pageNumber": page,
            "pageSize": page_size
        }
    )
    return resp.json()


def get_reservations_with_details(reservation_ids):
    """Fetch detailed info for a list of reservation IDs."""
    resp = requests.get(
        f"{BASE_URL}/getReservationsWithRateDetails",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={
            "propertyID": PROPERTY_ID,
            "reservationID": ",".join(reservation_ids)
        }
    )
    return resp.json()


def get_rate_plans(start_date, end_date):
    """Fetch rate plans with availability for date range."""
    resp = requests.get(
        f"{BASE_URL}/getRatePlans",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={
            "propertyID": PROPERTY_ID,
            "startDate": start_date,
            "endDate": end_date
        }
    )
    return resp.json()


def post_reservation(payload):
    """Create reservation. payload is a flat dict with bracket notation keys."""
    resp = requests.post(
        f"{BASE_URL}/postReservation",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data=payload
    )
    return resp.json()


def post_adjustment(reservation_id, amount, notes):
    """Post folio adjustment (negative amount for discount)."""
    resp = requests.post(
        f"{BASE_URL}/postAdjustment",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data={
            "propertyID": PROPERTY_ID,
            "reservationID": reservation_id,
            "type": "rate",
            "amount": amount,
            "notes": notes
        }
    )
    return resp.json()


def get_notes(reservation_id):
    """Fetch notes for a reservation."""
    resp = requests.get(
        f"{BASE_URL}/getReservationNotes",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"propertyID": PROPERTY_ID, "reservationID": reservation_id}
    )
    return resp.json()


def put_note(reservation_id, note_id, note):
    """Update an existing reservation note."""
    resp = requests.put(
        f"{BASE_URL}/putReservationNote",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data={
            "propertyID": PROPERTY_ID,
            "reservationID": reservation_id,
            "reservationNoteID": note_id,
            "reservationNote": note
        }
    )
    return resp.json()


def post_note(reservation_id, note):
    """Add note to reservation."""
    resp = requests.post(
        f"{BASE_URL}/postReservationNote",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data={
            "propertyID": PROPERTY_ID,
            "reservationID": reservation_id,
            "reservationNote": note
        }
    )
    return resp.json()
