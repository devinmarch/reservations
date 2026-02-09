import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from peewee import AutoField, TextField, IntegerField
from db import BaseModel, RoomStay
from devices import Lock


class CommonCode(BaseModel):
    id = AutoField()
    reservation_id = TextField()
    lock_id = IntegerField()
    seam_access_code_id = TextField(null=True)


def run():
    load_dotenv()

    TZ = ZoneInfo("America/St_Johns")

    common_locks = [
        {"id": d.id, "device": d.device_id, "key": os.environ.get(d.api_key_env)}
        for d in Lock.select().where(Lock.category == "common")
    ]

    if not common_locks:
        print("No common locks configured")
        return

    # Active reservation IDs from RoomStay
    active = (
        RoomStay.select(RoomStay.reservation_id, RoomStay.res_check_in, RoomStay.res_check_out)
        .where(RoomStay.res_status.in_(["confirmed", "checked_in"]))
    )
    active_res = {}
    for stay in active:
        if stay.reservation_id not in active_res:
            active_res[stay.reservation_id] = stay

    # Phase 1: Delete codes for reservations no longer active
    to_delete = CommonCode.select().where(
        CommonCode.reservation_id.not_in(list(active_res.keys()))
        & CommonCode.seam_access_code_id.is_null(False)
    )

    for code in to_delete:
        lock = next((l for l in common_locks if l["id"] == code.lock_id), None)
        if not lock:
            code.delete_instance()
            continue
        resp = requests.post(
            "https://connect.getseam.com/access_codes/delete",
            headers={"Authorization": f"Bearer {lock['key']}"},
            json={"access_code_id": code.seam_access_code_id}
        )
        if resp.ok:
            print(f"Deleted common code {code.seam_access_code_id} for reservation {code.reservation_id}")
            code.delete_instance()
        else:
            print(f"Failed to delete common code for {code.reservation_id}: {resp.text}")

    # Delete records that never got a code installed
    deleted = CommonCode.delete().where(
        CommonCode.reservation_id.not_in(list(active_res.keys()))
        & CommonCode.seam_access_code_id.is_null()
    ).execute()
    if deleted:
        print(f"Cleaned up {deleted} common code records without Seam codes")

    # Phase 2: Create codes for active reservations on each common lock
    for res_id, stay in active_res.items():
        pin = res_id[-5:]
        starts_at = datetime.fromisoformat(stay.res_check_in).replace(hour=15, minute=30, tzinfo=TZ).isoformat()
        ends_at = datetime.fromisoformat(stay.res_check_out).replace(hour=11, minute=30, tzinfo=TZ).isoformat()

        for lock in common_locks:
            existing = CommonCode.get_or_none(
                (CommonCode.reservation_id == res_id) & (CommonCode.lock_id == lock["id"])
            )
            if existing and existing.seam_access_code_id:
                continue

            # Check for existing code on the device to adopt
            resp = requests.post(
                "https://connect.getseam.com/access_codes/list",
                headers={"Authorization": f"Bearer {lock['key']}"},
                json={"device_id": lock["device"]}
            )
            adopted = next((c for c in resp.json().get("access_codes", []) if c["code"] == pin), None)

            if adopted:
                CommonCode.replace(
                    reservation_id=res_id,
                    lock_id=lock["id"],
                    seam_access_code_id=adopted["access_code_id"]
                ).execute()
                print(f"Adopted existing common code for reservation {res_id} on lock {lock['id']}")
                continue

            if datetime.fromisoformat(stay.res_check_out) < datetime.now():
                continue

            resp = requests.post(
                "https://connect.getseam.com/access_codes/create",
                headers={"Authorization": f"Bearer {lock['key']}"},
                json={
                    "device_id": lock["device"],
                    "code": pin,
                    "name": f"Reservation {res_id}",
                    "starts_at": starts_at,
                    "ends_at": ends_at
                }
            )

            if resp.ok:
                code_id = resp.json()["access_code"]["access_code_id"]
                CommonCode.replace(
                    reservation_id=res_id,
                    lock_id=lock["id"],
                    seam_access_code_id=code_id
                ).execute()
                print(f"Created common code for reservation {res_id} on lock {lock['id']}")
            else:
                # Create record without code — retry next sync
                if not existing:
                    CommonCode.create(reservation_id=res_id, lock_id=lock["id"])
                print(f"Failed to create common code for {res_id}: {resp.text}")

    # Phase 3: Update time windows for existing codes
    has_code = CommonCode.select().where(CommonCode.seam_access_code_id.is_null(False))

    for code in has_code:
        stay = active_res.get(code.reservation_id)
        if not stay:
            continue
        lock = next((l for l in common_locks if l["id"] == code.lock_id), None)
        if not lock:
            continue

        starts_at = datetime.fromisoformat(stay.res_check_in).replace(hour=15, minute=30, tzinfo=TZ).isoformat()
        ends_at = datetime.fromisoformat(stay.res_check_out).replace(hour=11, minute=30, tzinfo=TZ).isoformat()

        resp = requests.post(
            "https://connect.getseam.com/access_codes/update",
            headers={"Authorization": f"Bearer {lock['key']}"},
            json={
                "access_code_id": code.seam_access_code_id,
                "starts_at": starts_at,
                "ends_at": ends_at
            }
        )
        if resp.ok:
            print(f"Updated common code dates for reservation {code.reservation_id}")
        else:
            print(f"Failed to update common code for {code.reservation_id}: {resp.text}")
