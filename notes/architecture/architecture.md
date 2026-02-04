# OTA Service Architecture

## Overview
Stateless service for OTA partners to view their reservations filtered by source.

## Flow

```
┌─────────┐    ┌───────┐    ┌───────┐    ┌───────────┐
│ Browser │───▶│ Caddy │───▶│ Flask │───▶│ Cloudbeds │
└─────────┘    └───────┘    └───────┘    └───────────┘
     │              │            │              │
     │  1. GET /ota │            │              │
     │─────────────▶│            │              │
     │              │            │              │
     │  2. basicauth│            │              │
     │◀────────────▶│            │              │
     │              │            │              │
     │              │ 3. X-Remote-User: maxxim  │
     │              │───────────▶│              │
     │              │            │              │
     │              │            │ 4. getReservations (paginated)
     │              │            │─────────────▶│
     │              │            │◀─────────────│
     │              │            │              │
     │              │            │ 5. getReservationsWithRateDetails
     │              │            │─────────────▶│
     │              │            │◀─────────────│
     │              │            │              │
     │              │ 6. HTML    │              │
     │◀─────────────│◀───────────│              │
```

## Components

| Component | File | Purpose |
|-----------|------|---------|
| Blueprint | ota.py | Route logic, API calls, HTML rendering |
| Config | ota_config.json | Username → user config (sourceID, displayName, etc.) |
| Auth | config/Caddyfile | Basic auth per user, header forwarding |

## User Config

```json
{
  "maxxim": {
    "sourceID": "ss-954000-1",
    "displayName": "Maxxim Vacations"
  },
  "dev": {
    "sourceID": "s-1175266",
    "displayName": "Dev Testing"
  }
}
```

| Field | Purpose |
|-------|---------|
| sourceID | Cloudbeds source filter |
| displayName | Page title (e.g., "Maxxim Vacations Reservations") |

Extensible - add fields as needed (e.g., `rateCalculation`, `commission`).

## API Calls

### 1. getReservations (filtered)
- Window: 30 days back, 730 days forward
- Pagination: 100 per page
- Filter: `sourceID` matches user's mapped value
- Returns: reservation IDs only

### 2. getReservationsWithRateDetails
- Input: comma-separated reservation IDs from step 1
- Returns: full reservation + room details

## Data Flow

```
getReservations ──▶ filter by sourceID ──▶ collect IDs
                                               │
                                               ▼
HTML table ◀── build rows ◀── getReservationsWithRateDetails
```

## Security

- Each OTA user has separate Caddy credentials
- Username forwarded to Flask via `X-Remote-User` header
- No database - fully stateless
- Users only see reservations from their source
