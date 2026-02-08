# sync.py Summary

A script that synchronizes reservations from the CloudBeds API into a local SQLite database and manages smart lock access codes via the Seam API.

## High-Level Flow

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  CloudBeds   │──────>│    SQLite    │──────>│   Seam API   │
│     API      │ fetch │   Database   │ manage│ (Smart Locks)│
└──────────────┘       └──────────────┘       └──────────────┘
```

## Sync Lifecycle

```
┌─────────────────────────────────────────────────┐
│              1. FETCH FROM CLOUDBEDS            │
│         (Lines 26-49)                           │
│                                                 │
│  getReservations ──> reservation IDs            │
│  getReservationsWithRateDetails ──> full data   │
└──────────────────────┬──────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────┐
│            2. SAVE TO DATABASE                  │
│         (Lines 52-79)                           │
│                                                 │
│  For each reservation + room:                   │
│    build stay_id ──> add to api_ids list        │
│    RoomStay.replace() ──> upsert to DB          │
└──────────────────────┬──────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────┐
│          3. DELETE STALE RECORDS                │
│         (Lines 81-107)                          │
│                                                 │
│  DB records NOT IN api_ids:                     │
│    ├─ Has lock code? ──> delete Seam code first │
│    │                     then delete DB row     │
│    └─ No lock code?  ──> bulk delete from DB    │
└──────────────────────┬──────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────┐
│        4. CREATE LOCK CODES                     │
│         (Lines 109-151)                         │
│                                                 │
│  Confirmed reservations without a code:         │
│    ├─ Existing Seam code with same PIN? Adopt it│
│    └─ Otherwise ──> create new Seam code        │
└──────────────────────┬──────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────┐
│        5. UPDATE LOCK DATES                     │
│         (Lines 153-175)                         │
│                                                 │
│  All records with a Seam code:                  │
│    ──> update starts_at / ends_at on Seam       │
└─────────────────────────────────────────────────┘
```

## Detailed Breakdown

### Setup (Lines 1-24)

Loads environment variables, reads lock configuration from `lock_config.json`, and defines the sync window:
- **7 days back** and **7 days ahead** from today
- Timezone set to `America/St_Johns`

`LOCKS` is a dictionary mapping room IDs to their Seam device ID and API key, built from `lock_config.json`.

### Step 1: Get Reservation IDs (Lines 26-39)

Calls `getReservations` on the CloudBeds API filtered by:
- `propertyID`
- `roomTypeID`
- `checkInFrom` / `checkInTo` (the 7-day window)

Extracts all `reservationID` values into a comma-separated string for the next call.

### Step 2: Get Full Details & Save (Lines 41-79)

Calls `getReservationsWithRateDetails` with the reservation IDs from Step 1.

For each reservation and each room within it:
- Builds a `stay_id` (`reservationID_roomID`) as the unique key
- Collects all `stay_id` values into an `api_ids` list (used later for deletion)
- Uses `RoomStay.replace()` to insert or update the record in the database
- Preserves any existing `seam_access_code_id` so lock codes aren't lost on update

### Step 3: Delete Stale Records (Lines 81-107)

Removes any database records whose `id` is **not in** the `api_ids` list (i.e., no longer returned by the API). Split into two paths:

```
Records NOT IN api_ids
        │
        ├── Has seam_access_code_id?
        │     YES ──> Delete Seam code via API
        │             Then delete DB row (Lines 82-100)
        │
        └── No seam_access_code_id?
              ──> Bulk delete from DB (Lines 103-107)
```

**With Seam codes (Lines 82-100):**
- Queries for records not in `api_ids` that have a `seam_access_code_id`
- Deletes the physical lock code via Seam API first
- Then deletes the database row with `stay.delete_instance()`

**Without Seam codes (Lines 103-107):**
- Bulk deletes records not in `api_ids` that have no lock code
- Uses `RoomStay.delete().where(...).execute()`

### Step 4: Create Seam Access Codes (Lines 109-151)

Finds confirmed reservations that:
- Have no `seam_access_code_id` yet
- Are in a room that has a configured lock

```
Confirmed + No code + Has lock config
        │
        ├── Existing Seam code with same PIN?
        │     YES ──> Adopt it (save access_code_id)
        │
        └── No existing code?
              ──> Create new Seam code
                  PIN = last 5 digits of reservation ID
                  starts_at = check-in day @ 3:30 PM
                  ends_at = check-out day @ 11:30 AM
```

### Step 5: Update Seam Code Dates (Lines 153-175)

For all records that have a Seam code, sends an update to Seam with the current check-in/check-out times. This keeps lock schedules in sync if reservation dates change in CloudBeds.
