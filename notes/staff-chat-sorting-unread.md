# Staff Chat Portal - Sorting & Unread Indicators

## Overview
Two improvements for `/staff/chat`:
1. Sort conversations by most recent message (newest first)
2. Add unread message indicators

---

## Feature 1: Sort by Message Recency

### Current Behavior
Conversations sorted by `reservation_id` (alphabetical/numerical)

### Goal
Most recently messaged conversations at the top

### Implementation

**Add import:**
```python
from peewee import fn
```

**Replace query (lines 34-38 in server.py):**
```python
# Build dict of reservation_id -> last_sender
last_sender_map = {}
for msg in ChatMessage.select(ChatMessage.reservation_id, ChatMessage.sender, ChatMessage.created_at).order_by(ChatMessage.created_at):
    last_sender_map[msg.reservation_id] = msg.sender

# Get reservations with last message time
reservations = (
    RoomStay
    .select(
        RoomStay.reservation_id,
        RoomStay.guest_name,
        fn.MAX(ChatMessage.created_at).alias('last_msg_time')
    )
    .join(ChatMessage, on=(RoomStay.reservation_id == ChatMessage.reservation_id))
    .group_by(RoomStay.reservation_id)
    .order_by(fn.MAX(ChatMessage.created_at).desc())
)
```

**Key points:**
- Uses SQL JOIN to combine RoomStay + ChatMessage
- `fn.MAX(created_at)` gets most recent message timestamp
- `.desc()` sorts newest first
- No database changes needed - uses existing tables

---

## Feature 2: Unread Message Indicators

### Option A: Simple "Last Sender" Check (Recommended to start)

**Database changes:** None

**Logic:** Show indicator if last message is from guest

**Implementation:**
```python
# In the sidebar loop (line 40+):
sidebar = ""
for r in reservations:
    # Check if last message was from guest
    last_sender = last_sender_map.get(r.reservation_id, '')
    unread_dot = '<span class="unread-dot"></span>' if last_sender == 'guest' else ''
    sidebar += f'<div class="res" onclick="select(\'{r.reservation_id}\')">{unread_dot}{r.reservation_id}<br><small>{r.guest_name}</small></div>'
```

**Add CSS (after line 53):**
```css
.unread-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #0084ff;
    border-radius: 50%;
    margin-right: 8px;
}
```

**Pros:**
- Dead simple (~3 lines of code)
- No database changes
- Works well for small teams

**Cons:**
- Not accurate if staff viewed but didn't reply
- Disappears immediately when staff replies

---

### Option B: Track Last Viewed Timestamp (More accurate)

**Database changes:** Add new table

**In chat_db.py:**
```python
class StaffView(Model):
    reservation_id = TextField()
    last_viewed_at = DateTimeField()

    class Meta:
        database = db

# Update at bottom:
db.create_tables([ChatMessage, StaffView])
```

**Logic:** Track when staff opened each conversation, compare to message timestamps

**Add route to mark conversations as viewed:**
```python
@app.route("/staff/<reservation_id>/mark-viewed", methods=["POST"])
def mark_viewed(reservation_id):
    from datetime import datetime, timezone

    view = StaffView.get_or_none(StaffView.reservation_id == reservation_id)
    if view:
        view.last_viewed_at = datetime.now(timezone.utc)
        view.save()
    else:
        StaffView.create(
            reservation_id=reservation_id,
            last_viewed_at=datetime.now(timezone.utc)
        )
    return jsonify({"success": True})
```

**Update JavaScript select() function (line 75):**
```javascript
function select(resId) {
    currentRes = resId;

    // Record that staff viewed this conversation
    fetch(`/staff/${resId}/mark-viewed`, { method: 'POST' });

    // ... rest of existing code
}
```

**Update sidebar query:**
```python
sidebar = ""
for r in reservations:
    # Get last view time for this reservation
    view = StaffView.get_or_none(StaffView.reservation_id == r.reservation_id)
    last_viewed = view.last_viewed_at if view else None

    # Check if there are unread messages
    has_unread = False
    if last_viewed:
        unread_count = ChatMessage.select().where(
            (ChatMessage.reservation_id == r.reservation_id) &
            (ChatMessage.sender == 'guest') &
            (ChatMessage.created_at > last_viewed)
        ).count()
        has_unread = unread_count > 0
    else:
        # Never viewed - check if there are any guest messages
        has_unread = ChatMessage.select().where(
            (ChatMessage.reservation_id == r.reservation_id) &
            (ChatMessage.sender == 'guest')
        ).count() > 0

    unread_dot = '<span class="unread-dot"></span>' if has_unread else ''
    sidebar += f'<div class="res" onclick="select(\'{r.reservation_id}\')">{unread_dot}{r.reservation_id}<br><small>{r.guest_name}</small></div>'
```

**Pros:**
- Very accurate
- Shows unread even after staff replies
- Matches professional messaging app behavior

**Cons:**
- Requires new database table
- ~50 lines of code
- More complex

---

## Comparison Table

| Feature | Option A | Option B |
|---------|----------|----------|
| Database change | None | Add StaffView table |
| Lines of code | ~20 | ~50 |
| Accuracy | Good enough | Very accurate |
| Shows unread after staff reply | No | Yes |
| Best for | Small teams, one person | Multiple staff, professional use |

---

## Implementation Order

1. **Start with:** Sort by recency + Option A (simple unread)
   - Get both features working quickly
   - No database changes
   - ~25 lines of code total

2. **Upgrade later if needed:** Switch to Option B
   - If you find Option A isn't accurate enough
   - Easy to add later - just extends existing code

---

## Files to Modify

**For sorting + Option A:**
- `/Users/devinmarch/reservations/server.py` (lines 1, 34-53)

**For Option B (add these):**
- `/Users/devinmarch/reservations/chat_db.py` (add StaffView model)
- `/Users/devinmarch/reservations/server.py` (add mark-viewed route + update query)

---

## Notes

- All changes are in Python code, no frontend template changes needed (except CSS)
- The blue dot color (#0084ff) matches existing brand color
- 8px dot is standard convention (not required, just common practice)
- Option A is recommended starting point - upgrade to B if needed later
