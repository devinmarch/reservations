# Guest Chat Feature

## Overview
Two-way chat between guests and staff, built with a separate SQLite database to keep chat data isolated from the main reservations DB (avoids logging concerns).

## Current Implementation

### Database
- **chat_db.py** (root) — Separate `chat.db` SQLite file
- **ChatMessage model**: id (auto PK), reservation_id, sender ("guest" or "staff"), message, created_at

### Guest Side (guest/ blueprint)
- **GET /guest/<reservation_id>/chat** — Renders the chat UI
- **GET /guest/<reservation_id>/messages** — JSON endpoint returning all messages (used by poll)
- **POST /guest/<reservation_id>/messages** — Guest submits a message (hardcodes sender as "guest")
- **Template**: guest/templates/chat.html — Mobile-responsive chat UI styled like iMessage
- Poll interval: 3 seconds

### Staff Side (server.py)
- **GET /staff/chat** — Dashboard with reservation list sidebar + chat panel
- **POST /staff/<reservation_id>/messages** — Staff replies (hardcodes sender as "staff")
- Sidebar lists all reservations (deduplicated) with guest names
- Reuses the guest GET /messages endpoint to fetch conversation
- Poll interval: 3 seconds

### Key Design Decisions
- Separate DB keeps chat isolated from reservations data
- Separate POST endpoints for guest/staff so neither side can spoof the other's sender
- Guest URLs are tokenized via reservation_id (same ID used in /guest/<reservation_id>)
- Staff dashboard lives in server.py (not its own blueprint) since it's just 2 routes for now

## Future Ideas
- **Discord integration** — Guest chats populate as threads in a Discord channel; staff replies in Discord get routed back to the guest chat
- **Common staff dashboard** — More full-featured alternative to Discord approach
- Extract staff chat into its own blueprint if it grows
- Guest portal features beyond chat (check-in confirmation, receipts, etc.)
