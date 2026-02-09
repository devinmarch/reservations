from db import db
from devices import Lock

db.create_tables([Lock])

Lock.insert_many([
    {"room_id": "lobby", "device_id": "9ebcd933-4467-46a4-9e7a-a6a8bb39e208", "api_key_env": "SEAM_KEY_1", "category": "common"},
    {"room_id": "laundry", "device_id": "93fe3a3a-b9a6-435b-b717-fe204b5f2cb6", "api_key_env": "SEAM_KEY_1", "category": "common"},
]).execute()

print(f"Seeded {Lock.select().count()} locks")