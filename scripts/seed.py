from db import db
from devices import Device

db.create_tables([Device])

Device.insert_many([
    {"room_id": "537928-1", "device_id": "e90f7dd1-...", "api_key_env": "SEAM_KEY_1"},
    {"room_id": "537928-2", "device_id": "167e2aac-...", "api_key_env": "SEAM_KEY_1"},
    {"room_id": "537928-3", "device_id": "41be7d28-...", "api_key_env": "SEAM_KEY_1"},
]).execute()

print(f"Seeded {Device.select().count()} devices")
