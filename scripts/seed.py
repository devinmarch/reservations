from db import db
from devices import Device

db.create_tables([Device])

Device.insert_many([
    {"room_id": "537928-1", "device_id": "64c74161-80e9-4877-83fc-7b38b7e4cdce", "api_key_env": "SEAM_KEY_1"},
    {"room_id": "537928-2", "device_id": "4dc2c282-85ce-459d-8b89-e8ac254d5a4a", "api_key_env": "SEAM_KEY_1"},
    {"room_id": "537928-3", "device_id": "b2c8ebef-d4b1-4077-ac30-c588daa715eb", "api_key_env": "SEAM_KEY_1"},
]).execute()

print(f"Seeded {Device.select().count()} devices")
