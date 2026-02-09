import os
import random
import requests
from flask import Blueprint, request, jsonify
from peewee import AutoField, TextField, IntegerField
from db import BaseModel
from devices import Lock
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

room_block_bp = Blueprint('room_block', __name__, url_prefix='/room-block')

TZ = ZoneInfo("America/St_Johns")


class RoomBlockCode(BaseModel):
    id = AutoField()
    room_block_id = TextField()
    seam_code_id = TextField()
    lock_id = IntegerField()


@room_block_bp.route('/created', methods=['POST'])
def created():
    data = request.get_json()

    if data.get("roomBlockType") != "out_of_service":
        return jsonify({"skipped": True}), 200
    if data.get("roomBlockReason") != "hairycat":
        return jsonify({"skipped": True}), 200

    room_id = data["rooms"][0]["roomID"]
    lock = Lock.get_or_none(Lock.room_id == str(room_id))
    if not lock:
        return jsonify({"error": "No lock found for room"}), 404

    pin = str(random.randint(1000, 9999))
    starts_at = datetime.fromisoformat(data["startDate"]).replace(hour=0, minute=1, tzinfo=TZ).isoformat()
    ends_at = datetime.fromisoformat(data["endDate"]).replace(hour=23, minute=59, tzinfo=TZ).isoformat()

    seam_key = os.environ.get(lock.api_key_env)
    resp = requests.post(
        "https://connect.getseam.com/access_codes/create",
        headers={"Authorization": f"Bearer {seam_key}"},
        json={
            "device_id": lock.device_id,
            "code": pin,
            "name": "hairycat",
            "starts_at": starts_at,
            "ends_at": ends_at
        }
    )
    seam_code_id = resp.json()["access_code"]["access_code_id"]

    RoomBlockCode.create(
        room_block_id=data["roomBlockID"],
        seam_code_id=seam_code_id,
        lock_id=lock.id
    )

    api_key = os.environ.get("CLOUDBEDS_API_KEY")
    property_id = os.environ.get("CLOUDBEDS_PROPERTY_ID")
    requests.put(
        "https://api.cloudbeds.com/api/v1.2/putRoomBlock",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "propertyID": property_id,
            "roomBlockID": data["roomBlockID"],
            "roomBlockReason": f"Code: {pin}"
        }
    )

    return jsonify({"success": True, "code": pin}), 201


@room_block_bp.route('/deleted', methods=['POST'])
def deleted():
    data = request.get_json()

    record = RoomBlockCode.get_or_none(RoomBlockCode.room_block_id == data["roomBlockID"])
    if not record:
        return jsonify({"skipped": True}), 200

    lock = Lock.get_or_none(Lock.id == record.lock_id)
    if lock:
        seam_key = os.environ.get(lock.api_key_env)
        requests.post(
            "https://connect.getseam.com/access_codes/delete",
            headers={"Authorization": f"Bearer {seam_key}"},
            json={"access_code_id": record.seam_code_id}
        )

    record.delete_instance()
    return jsonify({"success": True}), 200
