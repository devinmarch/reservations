# OTA Service Implementation Plan

## Overview
New standalone service at `/ota` for viewing OTA reservations filtered by source. Uses Flask Blueprints for isolation.

## User → sourceID Mapping
| User   | sourceID      |
|--------|---------------|
| maxxim | ss-954000-1   |
| dev    | s-1175266     |

## Files to Create

### 1. ota.py
Single-file Blueprint containing:
- Blueprint definition (`ota_bp`)
- `/ota` route with all logic:
  - Loads env vars: CLOUDBEDS_API_KEY, CLOUDBEDS_PROPERTY_ID
  - Loads ota_config.json for username → sourceID mapping
  - Reads X-Remote-User header (forwarded by Caddy)
  - Paginates getReservations (2 year window, 100/page)
  - Filters by source.sourceID matching user's mapped value
  - Fetches full details with getReservationsWithRateDetails
  - Renders HTML table

Why single file: One route, stateless, self-contained. No need for directory structure.

### 2. ota_config.json
```json
{
  "maxxim": "ss-954000-1",
  "dev": "s-1175266"
}
```

## Files to Modify

### 4. server.py
Add 2 lines:
```python
from ota import ota_bp
app.register_blueprint(ota_bp)
```

### 5. config/Caddyfile
Add /ota protection and header forwarding:
```
@ota path /ota*
basicauth @ota {
    maxxim $hashed_password
    dev $hashed_password
}
header_up X-Remote-User {http.auth.user.id}
```

## No Changes Required to Existing Services
- sync.py: No changes (standalone script, not a route)
- db.py: No changes (OTA service is stateless, no database)
- Existing routes (/, /sync, /r/<id>): No changes needed

Blueprint registration is additive - it doesn't affect existing routes.

## API Flow

```
1. User visits /ota
2. Caddy prompts for basicauth
3. Caddy forwards authenticated username in X-Remote-User header
4. Flask /ota route:
   a. Read X-Remote-User header
   b. Look up sourceID from ota_config.json
   c. Calculate date window (1 year back, 1 year forward)
   d. Loop through getReservations pages:
      - GET /getReservations?page=N&pageSize=100&checkInFrom=X&checkInTo=Y
      - Filter results where source.sourceID == user's sourceID
      - Collect matching reservationIDs
   e. GET /getReservationsWithRateDetails with collected IDs
   f. Render HTML table
5. Display table with reservation + room rows
```

## Table Structure

| reservationID | thirdPartyIdentifier | reservationCheckIn | reservationCheckOut | total |
|---------------|----------------------|--------------------|---------------------|-------|
| 2187044465114 | HM12345              | 2026-02-06         | 2026-02-08          | 448.50|
| └─ Lodge Room with Shared Sauna, 2 adults |||||

## Dependencies
- requests (already in requirements.txt)
- python-dotenv (already in requirements.txt)
- No new dependencies required
