from peewee import SqliteDatabase, Model, AutoField, TextField, DateTimeField
from datetime import datetime, timezone

db = SqliteDatabase("chat.db")


class ChatMessage(Model):
    id = AutoField()
    reservation_id = TextField()
    sender = TextField()  # "guest" or "staff"
    message = TextField()
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        database = db

db.create_tables([ChatMessage])
