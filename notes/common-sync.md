# Common Lock Sync Service

Manages Seam access codes on shared/common locks (lobby, laundry, etc.) for active reservations.

## How It Fits In

```
Guest books reservation
        |
        v
  +-----------+       +------------------+
  | Cloudbeds  | ----> | Room Sync        |  (reservations/sync.py)
  | API        |       | Updates RoomStay |
  +-----------+       +------------------+
                              |
                              | calls at end of sync
                              v
                      +------------------+
                      | Common Sync      |  (reservations/common_sync.py)
                      | Updates CommonCode|
                      +------------------+
                              |
                              v
                        +----------+
                        | Seam API |  install/update/delete codes
                        +----------+
```

## Data Model

**CommonCode table** (defined in `reservations/common_sync.py`)

| Field               | Type      | Description                                     |
|---------------------|-----------|-------------------------------------------------|
| id                  | AutoField | Auto-incrementing primary key                   |
| reservation_id      | TextField | Cloudbeds reservation ID                        |
| lock_id             | Integer   | References Lock table primary key (7-digit int) |
| seam_access_code_id | TextField | Seam access code ID, null = not yet installed   |

Each row represents one code on one common lock for one reservation.

**Relationship to other tables:**

```
Lock (category="common")        RoomStay (status=confirmed/checked_in)
  |                                |
  | lock_id                        | reservation_id
  v                                v
+----------------------------------------------------+
|                  CommonCode                         |
|  reservation_id  |  lock_id  |  seam_access_code_id |
+----------------------------------------------------+
```

If there are 3 active reservations and 2 common locks, there will be 6 CommonCode rows (3 x 2).

## Sync Phases

### Phase 1: Delete

Removes codes for reservations that are no longer active (cancelled, checked out, or no longer in the sync window).

```
CommonCode records
where reservation_id NOT IN active reservations
        |
        |-- has seam_access_code_id? --> call Seam DELETE
        |       |-- success --> delete row
        |       |-- failure --> leave for retry
        |
        |-- no seam_access_code_id? --> delete row (nothing to clean up)
```

Also handles the case where a common lock is removed from the Lock table — if the lock_id no longer matches any common lock, the record is deleted without calling Seam (the device is gone).

### Phase 2: Create (with Adopt)

Installs codes on every common lock for every active reservation.

```
For each active reservation:
  For each common lock:
        |
        |-- CommonCode row exists with code? --> skip
        |
        |-- List existing codes on device (Seam API)
        |       |-- matching PIN found? --> adopt it (save code ID)
        |
        |-- checkout already passed? --> skip
        |
        |-- Create new code (Seam API)
                |-- success --> save code ID to CommonCode
                |-- failure --> create row with null code (retry next sync)
```

**PIN**: Last 5 digits of reservation_id (same as room locks)
**Time window**: res_check_in at 3:30 PM to res_check_out at 11:30 AM (Newfoundland time)

The adopt step is important for self-healing. If a code already exists on the physical lock (e.g. from a manual install or a previous sync that crashed mid-way), the service finds it by matching the PIN and links it rather than creating a duplicate.

### Phase 3: Update

Keeps time windows current in case reservation dates change.

```
For each CommonCode with a seam_access_code_id:
        |
        |-- reservation still active? --> call Seam UPDATE with current dates
        |-- reservation gone? --> skip (Phase 1 handles deletion)
```

## Self-Healing Behaviors

| Scenario                          | What Happens                                                    |
|-----------------------------------|-----------------------------------------------------------------|
| Seam create fails                 | Row created with null code, retried next sync                   |
| Seam delete fails                 | Row kept, retried next sync                                     |
| Code exists on lock already       | Adopted by matching PIN, no duplicate created                   |
| New common lock added             | Next sync creates codes for all active reservations on it       |
| Common lock removed from DB       | Orphaned CommonCode rows deleted (lock_id no longer matches)    |
| Reservation cancelled mid-stay    | Phase 1 deletes codes on all common locks for that reservation  |

## File Locations

| File                          | Role                                          |
|-------------------------------|-----------------------------------------------|
| `reservations/common_sync.py` | CommonCode model + sync logic                 |
| `reservations/sync.py`        | Room sync, calls common sync at end (line 182)|
| `server.py`                   | Registers CommonCode in create_tables         |
| `devices/__init__.py`         | Lock model (category field identifies common) |
