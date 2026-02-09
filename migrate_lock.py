from playhouse.migrate import SqliteMigrator, migrate
from peewee import SqliteDatabase, TextField

db = SqliteDatabase("hotel-automation.db")
migrator = SqliteMigrator(db)

migrate(
    migrator.add_column('lock', 'category', TextField(null=True)),
    migrator.drop_not_null('lock', 'room_id'),
)

print("Migration complete: added 'category' column, made 'room_id' nullable")
