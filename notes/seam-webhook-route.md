# Seam Webhook Route

A single Flask route that receives webhook events from Seam and processes them inline.

## How It Works

```
Seam Event ──> POST /webhook/seam ──> Flask Route ──> if/elif ──> DB Update
```

Seam sends a POST request to your server whenever something happens with an access code (set on lock, removed, failed, etc.). The route inspects the `event_type` field and handles each event in its own branch.

## Flow

```
┌──────────┐         ┌──────────────────────┐         ┌──────────┐
│   Seam   │──POST──>│  /webhook/seam       │──query──>│  SQLite  │
│  Server  │         │  (Flask route)       │──update──>│    DB    │
└──────────┘         └──────────────────────┘         └──────────┘
                              │
                     ┌────────┴────────┐
                     │   event_type?   │
                     ├─────────────────┤
                     │                 │
                ┌────┴────┐     ┌─────┴─────┐
                │  "set"  │     │ "removed" │
                │         │     │           │
                │ Update  │     │  Update   │
                │ status  │     │  status   │
                │ to set  │     │ to removed│
                └─────────┘     └───────────┘
```

## Example Implementation

```python
@app.route("/webhook/seam", methods=["POST"])
def seam_webhook():
    event = request.json
    event_type = event["event_type"]

    if event_type == "access_code.set_on_device":
        code_id = event["payload"]["access_code_id"]
        stay = RoomStay.get_or_none(RoomStay.seam_access_code_id == code_id)
        if stay:
            stay.code_status = "set"
            stay.save()

    elif event_type == "access_code.removed_from_device":
        code_id = event["payload"]["access_code_id"]
        stay = RoomStay.get_or_none(RoomStay.seam_access_code_id == code_id)
        if stay:
            stay.code_status = "removed"
            stay.save()

    return "", 200
```

## Key Details

- **One route, multiple events** — The route acts as both router and processor. Each `if/elif` branch is self-contained.
- **Query by non-key field** — Looks up the RoomStay by `seam_access_code_id` (not the primary key), since that's what Seam knows about.
- **Always return 200** — Even for unrecognized events. If you return an error, Seam may retry the webhook repeatedly.
- **Caddy exposure** — The endpoint needs to be publicly accessible (no BasicAuth) so Seam can reach it. Consider verifying the request is actually from Seam (e.g., checking a shared secret or Seam's webhook signature).

## Requires

- A `code_status` field on the `RoomStay` model (added via Peewee migration)
- A webhook configured in the Seam dashboard pointing to your server's `/webhook/seam` URL
