# OTA Refactor + Create Reservation Plan

## Directory Structure

```
ota/
  __init__.py       # Blueprint definition + route handlers
  api.py            # CloudBeds API wrapper functions
  templates/
    list.html       # Reservation table + embedded create modal
  static/
    ota.js          # Form interactions for create reservation
```

## Config Changes (ota_config.json)

```json
{
  "defaults": {
    "country": "CA",
    "taxRate": 0.15
  },
  "roomTypes": {
    "537927": { "name": "Lodge Suite", "maxGuests": 2, "rateID": "1677951" },
    "537928": { "name": "Lodge Room", "maxGuests": 2, "rateID": "1677952" }
  },
  "users": {
    "maxxim": {
      "sourceID": "ss-954000-1",
      "displayName": "Maxxim Vacations",
      "phone": "",
      "email": "maxxim@devinmarch.com",
      "adjustmentModel": "percentage",
      "adjustmentPercent": 0.15,
      "otaRates": { "537927": 200.00, "537928": 100.00 }
    },
    "dev": {
      "sourceID": "s-1175266",
      "displayName": "Dev Testing",
      "phone": "",
      "email": "dev@devinmarch.com",
      "adjustmentModel": "percentage",
      "adjustmentPercent": 0.15,
      "otaRates": {}
    }
  }
}
```

**Config Design:**
- `rateID` lives in `roomTypes` (global, 1:1 with room type)
- `otaRates` per user serves dual purpose: keys = allowed rooms, values = OTA-specific pricing
- Presence in `otaRates` grants access to that room type

**Adjustment Models:**
- `"percentage"` → applies `adjustmentPercent` to net total (grandTotal / 1.15)
- `"otaRate"` → calculates adjustment from `(cloudbedsRate - otaRate) * nights` per room

## Files to Create

### 1. ota/__init__.py
Routes:
- `GET /ota` – List reservations (current logic, renders list.html)
- `POST /ota/availability` – Calls getRatePlans, returns JSON
- `POST /ota/create` – Creates reservation, adjusts folio, posts note, redirects

### 2. ota/api.py
Functions wrapping CloudBeds API:
- `get_reservations(check_in_from, check_in_to, page)` – paginated fetch
- `get_reservations_with_details(reservation_ids)` – bulk details
- `get_rate_plans(check_in, check_out, rate_ids)` – availability check
- `post_reservation(payload)` – create reservation
- `post_adjustment(reservation_id, amount, description)` – folio adjustment
- `post_note(reservation_id, note)` – add note to reservation

### 3. ota/templates/list.html
- Reservation table with Jinja2 loop
- "Create Reservation" button in header
- Embedded modal (no separate create.html)
- CSS for modal, buttons, form layout
- Passes ROOM_TYPES to JS, loads ota.js

### 4. ota/static/ota.js
Handles:
- Modal open/close
- Date validation (check-out > check-in)
- Check Availability button → fetch /ota/availability → populate results
- Add Room button → append room row, enforce inventory limits
- Remove room functionality
- Confirm button → fetch /ota/create → handle response/redirect

## Files to Modify

### server.py
Change import:
```python
# Before
from ota import ota_bp

# After
from ota import ota_bp
```
(No change needed if __init__.py exports ota_bp)

### ota_config.json
Restructure as shown above.

## API Flow for Create Reservation

```
1. User opens modal, enters dates
2. Click "Check Availability"
   → POST /ota/availability { checkIn, checkOut }
   → Backend calls getRatePlans with user's rateIDs
   → Returns available rooms + quantities

3. User adds rooms, fills guest info
4. Click "Confirm Reservation"
   → POST /ota/create { checkIn, checkOut, rooms[], guest, notes }
   → Backend:
     a. Re-call getRatePlans to verify availability
     b. If unavailable → return error
     c. Call postReservation
     d. Calculate adjustment: grandTotal / 1.15 * adjustmentPercent
     e. Call postAdjustment with negative amount
     f. Call postNote with user's notes
     g. Return success
   → Frontend: flash message, redirect to /ota
```

## Questions to Resolve

1. ~~What are the actual room type IDs and rate IDs to put in the config?~~ **Resolved: 537927/537928, 1677951/1677952**
2. ~~What adjustment percentage should we use initially?~~ **Resolved: 15%**
3. ~~Should the modal be a separate page instead of a popup?~~ **Resolved: Modal popup**

## Order of Implementation

1. ~~Refactor: Create ota/ directory, move existing logic, verify listing still works~~ **DONE**
2. ~~Expand config file structure~~ **DONE**
3. ~~Add api.py with CloudBeds wrapper functions (listing only)~~ **DONE**
4. ~~Build create.html form structure~~ **DONE** (modal embedded in list.html)
5. ~~Build ota.js interactions~~ **DONE**
6. ~~Add /ota/availability route + get_rate_plans() in api.py~~ **DONE**
7. Add /ota/create route + post_reservation(), post_adjustment(), post_note() in api.py **← NEXT**
8. Test end-to-end

## Completed Work (2026-02-04)

### Refactor Summary (Steps 1-3)
- Created `ota/` directory structure with `__init__.py`, `api.py`, `templates/`, `static/`
- Extracted HTML into Jinja2 template `list.html`
- Moved API calls into `api.py` wrapper functions
- Updated `ota_config.json` with new nested structure (defaults, roomTypes, users)
- Deleted old `ota.py`
- No changes needed to `server.py` - import works automatically

### Frontend Complete (Steps 4-5)

**ota/templates/list.html** - Updated with:
- Header layout with "Create Reservation" button
- Full modal structure embedded (no separate create.html needed)
- CSS for modal, buttons, form layout, room entries
- Passes `ROOM_TYPES` to JS via `{{ room_types | tojson }}`
- Loads `ota.js` from static folder

**ota/static/ota.js** (~200 lines) - Handles:
- Modal open/close (click button, X, or overlay)
- `resetForm()` - clears state when modal opens
- Date validation (check-out must be after check-in)
- Check Availability → POST `/ota/availability` → renders results
- Tracks `availability = { roomTypeId: count }` state
- Add Room → creates dropdown with room types, respects remaining inventory
- Guest count dropdown populated from `ROOM_TYPES[id].maxGuests`
- `updateAllRoomDropdowns()` - recalculates "(X left)" labels when rooms change
- Remove room functionality
- Confirm → POST `/ota/create` with `{ checkIn, checkOut, firstName, lastName, otaRef, notes, rooms[] }`
- Success → `alert()` + `window.location.reload()`

**ota/__init__.py** - Updated to pass `room_types=CONFIG.get("roomTypes", {})` to template

### Current File Summary

| File | Lines | Status |
|------|-------|--------|
| `ota/__init__.py` | ~80 | Has GET /ota, POST /ota/availability |
| `ota/api.py` | ~50 | Has get_reservations, get_reservations_with_details, get_rate_plans |
| `ota/templates/list.html` | ~145 | Complete with modal |
| `ota/static/ota.js` | ~200 | Complete, waiting for /ota/create route |

### Step 6 Complete - Availability Route

**ota/api.py** - Added:
```python
def get_rate_plans(start_date, end_date):
    """Fetch rate plans with availability for date range."""
    # Calls CloudBeds getRatePlans API
    # Returns full response with data[] containing rateID, roomTypeID, roomsAvailable
```

**ota/__init__.py** - Added:
```python
@ota_bp.route('/ota/availability', methods=['POST'])
def check_availability():
    # 1. Get user from X-Remote-User header
    # 2. Get user's otaRates (keys = allowed room types)
    # 3. Build rateID → roomTypeID mapping from roomTypes config
    # 4. Call get_rate_plans(checkIn, checkOut)
    # 5. Filter results to user's allowed rooms
    # 6. Return { availability: { roomTypeId: count } }
```

### Still TODO in api.py (Step 7)

```python
def post_reservation(payload):
    """Create reservation. Returns response with reservationID, grandTotal"""
    pass

def post_adjustment(reservation_id, amount, description):
    """Post folio adjustment (negative amount for discount)"""
    pass

def post_note(reservation_id, note):
    """Add note to reservation"""
    pass
```

### Still TODO in __init__.py (Step 7)

```python
@ota_bp.route('/ota/create', methods=['POST'])
def create_reservation():
    # 1. Re-check availability via get_rate_plans()
    # 2. If unavailable → return error JSON
    # 3. Build payload, call post_reservation()
    # 4. Calculate adjustment: grandTotal / (1 + taxRate) * adjustmentPercent
    # 5. Call post_adjustment() with negative amount
    # 6. If notes provided, call post_note()
    # 7. Return success JSON
    pass
```

### Key Implementation Details for Backend

**Availability route expects:**
- Request: `{ checkIn: "YYYY-MM-DD", checkOut: "YYYY-MM-DD" }`
- Response: `{ availability: { "537927": 2, "537928": 1 } }`

**Create route expects:**
- Request: `{ checkIn, checkOut, firstName, lastName, otaRef, notes, rooms: [{ roomTypeId, guests }] }`
- Must re-verify availability before posting (prevent double-booking)
- sourceID for reservation = user's sourceID + "-1" suffix (e.g., "ss-954000-1-1")
- Adjustment calculation: `grandTotal / 1.15 * 0.15` (for 15% tax, 15% adjustment)
- Response: `{ success: true }` or `{ error: "message" }`

## Future Enhancements

### Table Sorting/Searching (deferred)
Options to consider:
- **Tablesort** (~2kb) - sorting only, dead simple
- **List.js** (~7kb) - sorting + searching
- **Server-side** - URL params, no JS but page reloads
