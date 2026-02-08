from peewee import SqliteDatabase, Model, AutoField, TextField, FloatField, DateTimeField
from playhouse.sqlite_ext import JSONField
from datetime import datetime, timezone

db = SqliteDatabase("hotel-automation.db")


class BaseModel(Model):
    class Meta:
        database = db


class RoomStay(BaseModel):
    id = TextField(primary_key=True)
    reservation_id = TextField()
    room_id = TextField(null=True)
    room_name = TextField(null=True)
    guest_name = TextField()
    room_status = TextField()
    room_check_in = TextField()
    room_check_out = TextField()
    res_check_in = TextField()
    res_check_out = TextField()
    res_status = TextField()
    balance = FloatField()
    date_modified = TextField()
    data = JSONField()
    seam_access_code_id = TextField(null=True)


class ChatMessage(BaseModel):
    id = AutoField()
    reservation_id = TextField()
    sender = TextField()
    message = TextField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
