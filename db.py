from peewee import SqliteDatabase, Model, TextField, FloatField
from playhouse.sqlite_ext import JSONField

db = SqliteDatabase("reservations.db")

class RoomStay(Model):
    id = TextField(primary_key=True)  # reservation_id + room_id
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

    class Meta:
        database = db

db.create_tables([RoomStay])
