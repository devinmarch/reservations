from flask import Blueprint, request, jsonify
from db import RoomStay, ChatMessage

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/chat")
def chat():
    reservations = (
        RoomStay.select(RoomStay.reservation_id, RoomStay.guest_name)
        .distinct()
        .order_by(RoomStay.reservation_id)
    )
    sidebar = ""
    for r in reservations:
        sidebar += f'<div class="res" onclick="select(\'{r.reservation_id}\')">{r.reservation_id}<br><small>{r.guest_name}</small></div>'

    return f"""<!DOCTYPE html>
<html><head><title>Staff Chat</title>
<style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    html, body {{ height:100%; font-family:-apple-system,system-ui,sans-serif; }}
    body {{ display:flex; }}
    #sidebar {{ width:260px; background:#2c2c2c; color:white; overflow-y:auto; flex-shrink:0; }}
    #sidebar h2 {{ padding:16px; font-size:16px; border-bottom:1px solid #444; }}
    .res {{ padding:12px 16px; border-bottom:1px solid #444; cursor:pointer; font-size:14px; }}
    .res:hover, .res.active {{ background:#444; }}
    .res small {{ opacity:0.7; }}
    #chat {{ flex:1; display:flex; flex-direction:column; background:#f5f5f5; }}
    #chat-header {{ padding:12px 16px; background:white; border-bottom:1px solid #ddd; font-weight:600; }}
    #messages {{ flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:6px; }}
    .msg {{ max-width:70%; padding:10px 14px; border-radius:18px; font-size:15px; line-height:1.4; word-wrap:break-word; }}
    .msg.guest {{ background:#e4e6eb; align-self:flex-start; border-bottom-left-radius:4px; }}
    .msg.staff {{ background:#0084ff; color:white; align-self:flex-end; border-bottom-right-radius:4px; }}
    .msg .time {{ font-size:11px; opacity:0.6; margin-top:4px; }}
    #input-bar {{ display:flex; padding:8px 12px; background:white; border-top:1px solid #ddd; gap:8px; }}
    #input-bar input {{ flex:1; padding:10px 16px; border:1px solid #ddd; border-radius:20px; outline:none; font-size:15px; }}
    #input-bar button {{ padding:10px 18px; background:#0084ff; color:white; border:none; border-radius:20px; cursor:pointer; font-size:15px; }}
    #placeholder {{ flex:1; display:flex; align-items:center; justify-content:center; color:#999; font-size:18px; }}
</style>
</head><body>
<div id="sidebar"><h2>Reservations</h2>{sidebar}</div>
<div id="chat">
    <div id="placeholder">Select a reservation</div>
</div>
<script>
    let currentRes = null;
    let poll = null;

    function select(resId) {{
        currentRes = resId;
        document.querySelectorAll('.res').forEach(el => el.classList.remove('active'));
        event.currentTarget.classList.add('active');

        document.getElementById('chat').innerHTML = `
            <div id="chat-header">Reservation: ${{resId}}</div>
            <div id="messages"></div>
            <div id="input-bar">
                <input type="text" id="msg" placeholder="Type a reply..." autocomplete="off">
                <button onclick="send()">Send</button>
            </div>
        `;
        document.getElementById('msg').addEventListener('keydown', e => {{ if (e.key === 'Enter') send(); }});

        if (poll) clearInterval(poll);
        loadMessages();
        poll = setInterval(loadMessages, 3000);
    }}

    function loadMessages() {{
        return fetch(`/guest/${{currentRes}}/messages`)
            .then(r => r.json())
            .then(msgs => {{
                const div = document.getElementById('messages');
                const atBottom = div.scrollHeight - div.scrollTop - div.clientHeight < 50;
                div.innerHTML = '';
                msgs.forEach(m => {{
                    const el = document.createElement('div');
                    el.className = 'msg ' + m.sender;
                    el.innerHTML = m.message + `<div class="time">${{m.sender}}</div>`;
                    div.appendChild(el);
                }});
                if (atBottom) div.scrollTop = div.scrollHeight;
            }});
    }}

    function send() {{
        const text = document.getElementById('msg').value.trim();
        if (!text) return;
        fetch(`/staff/${{currentRes}}/messages`, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{message: text}})
        }}).then(() => {{
            document.getElementById('msg').value = '';
            loadMessages().then(() => {{ document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight; }});
        }});
    }}
</script>
</body></html>"""


@staff_bp.route("/<reservation_id>/messages", methods=["POST"])
def post_message(reservation_id):
    data = request.get_json()
    ChatMessage.create(
        reservation_id=reservation_id,
        sender="staff",
        message=data.get("message", "").strip()
    )
    return jsonify({"success": True})
