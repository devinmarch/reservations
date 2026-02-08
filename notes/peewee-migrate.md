# Peewee Migrations

Peewee includes a built-in migration module (`playhouse.migrate`) for altering database tables without losing data.

## Why Migrations

When you add a field to your Peewee model, that only changes the Python code. The actual SQLite database file still has the old schema. A migration runs the `ALTER TABLE` SQL to add/remove/rename columns on the real database.

## Two Steps

```
1. Migration script  ──>  Alters the actual database file
2. Model edit        ──>  Updates db.py so Peewee knows about the new column
```

Both are needed. The migration changes the database; the model edit keeps your code in sync.

## Example: Adding a Column

### Step 1 — Migration Script

Create a file (e.g., `migrate_add_code_status.py`):

```python
from playhouse.migrate import SqliteMigrator, migrate
from peewee import TextField
from db import db

migrator = SqliteMigrator(db)
migrate(
    migrator.add_column("roomstay", "code_status", TextField(null=True))
)
print("Migration complete: added code_status column")
```

Run it once:

```bash
python migrate_add_code_status.py
```

### Step 2 — Update the Model

In `db.py`, add the field to the class:

```python
class RoomStay(Model):
    # ... existing fields ...
    seam_access_code_id = TextField(null=True)
    code_status = TextField(null=True)           # new field
```

## Common Migration Operations

```python
from playhouse.migrate import SqliteMigrator, migrate
from peewee import TextField, IntegerField

migrator = SqliteMigrator(db)

# Add a column
migrate(migrator.add_column("roomstay", "code_status", TextField(null=True)))

# Drop a column
migrate(migrator.drop_column("roomstay", "old_field"))

# Rename a column
migrate(migrator.rename_column("roomstay", "old_name", "new_name"))

# Add an index (for faster queries on a column)
migrate(migrator.add_index("roomstay", ("seam_access_code_id",), unique=False))
```

## Important Notes

- **`null=True` on new columns** — Existing rows need a value for the new column. `null=True` means they get `NULL`. Without it, the migration fails because existing rows have no value.
- **Run once** — Migration scripts alter the database schema. Running the same one twice will error (column already exists).
- **Keep or delete** — After running, migration scripts are just for reference. You can keep them in a `migrations/` folder or delete them.
- **No auto-detection** — Unlike Flask-Migrate/Alembic, Peewee does not auto-detect model changes. You write the migration manually. For a small project with infrequent schema changes, this is fine.
- **Backup first** — Before running a migration on production, copy your `.db` file. SQLite migrations are not reversible by default.
