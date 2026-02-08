from db import db
from devices import Lock

db.create_tables([Lock])

Lock.insert_many([
    {"room_id": "537928-1", "device_id": "e90f7dd1-18fd-4f43-9520-dc1aaad225c6", "api_key_env": "SEAM_KEY_1"},
    {"room_id": "537928-2", "device_id": "167e2aac-74d4-4049-a26d-6fb0234cc57c", "api_key_env": "SEAM_KEY_1"},
    {"room_id": "537928-3", "device_id": "41be7d28-9fe1-41bb-aed8-553e993bbd26", "api_key_env": "SEAM_KEY_1"},
]).execute()

print(f"Seeded {Lock.select().count()} locks")
