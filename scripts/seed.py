from db import db
from devices import Device

db.create_tables([Device])

Device.insert_many([
    "537928-1": {"device": "e90f7dd1-18fd-4f43-9520-dc1aaad225c6", "key": "SEAM_KEY_1"},
    "537928-2": {"device": "167e2aac-74d4-4049-a26d-6fb0234cc57c", "key": "SEAM_KEY_1"},
    "537928-3": {"device": "41be7d28-9fe1-41bb-aed8-553e993bbd26", "key": "SEAM_KEY_1"}
]).execute()

print(f"Seeded {Device.select().count()} devices")
