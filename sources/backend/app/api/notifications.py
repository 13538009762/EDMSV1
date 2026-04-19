from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.notification import Notification
from app.utils.auth import current_user

bp = Blueprint("notifications", __name__)

@bp.get("")
@jwt_required()
def list_notifications():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get last 50 notifications
    nots = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(50).all()
    
    items = []
    for n in nots:
        items.append({
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "type": n.type,
            "is_read": n.is_read,
            "link_url": n.link_url,
            "created_at": n.created_at.isoformat() + "Z" if n.created_at else None
        })
        
    return jsonify({
        "items": items,
        "unread_count": sum(1 for n in items if not n["is_read"])
    })

@bp.post("/<int:id>/read")
@jwt_required()
def mark_read(id: int):
    user = current_user()
    n = db.session.get(Notification, id)
    if not n or n.user_id != user.id:
        return jsonify({"error": "Not found"}), 404
        
    n.is_read = True
    db.session.commit()
    return jsonify({"success": True})

@bp.post("/read-all")
@jwt_required()
def mark_all_read():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})
