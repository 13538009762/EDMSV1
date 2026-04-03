"""Relay Yjs updates and editor awareness between clients."""
from flask import request
from flask_socketio import emit, join_room, leave_room

from app.extensions import socketio


@socketio.on("join_document")
def on_join_document(data):
    # 鉴权可在此校验 JWT；演示环境由前端自律
    did = data.get("document_id")
    if did is None:
        return
    room = f"doc_{did}"
    join_room(room)
    emit("joined", {"room": room}, room=request.sid)


@socketio.on("leave_document")
def on_leave_document(data):
    did = data.get("document_id")
    if did is None:
        return
    leave_room(f"doc_{did}")


@socketio.on("yjs_update")
def on_yjs_update(data):
    did = data.get("document_id")
    payload = data.get("payload")
    if did is None:
        return
    emit(
        "yjs_update",
        {"document_id": did, "payload": payload},
        room=f"doc_{did}",
        skip_sid=request.sid,
    )


@socketio.on("awareness_update")
def on_awareness(data):
    did = data.get("document_id")
    payload = data.get("payload")
    if did is None:
        return
    emit(
        "awareness_update",
        {"document_id": did, "payload": payload, "sid": request.sid},
        room=f"doc_{did}",
        skip_sid=request.sid,
    )
