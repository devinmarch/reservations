import random
from peewee import TextField, IntegerField
from db import BaseModel


class Device(BaseModel):
    id = IntegerField(primary_key=True, default=lambda: random.randint(1000000, 9999999))
    room_id = TextField()
    device_id = TextField()
    api_key_env = TextField()
