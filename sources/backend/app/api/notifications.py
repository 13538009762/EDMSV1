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
    
    # notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(50).all()

    try:
        # Get last 50 notifications
        nots = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(50).all()
        
        return jsonify({
            "items": [n.to_dict() for n in nots],
            "unread_count": sum(1 for n in nots if not n.is_read)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

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

@bp.post("/<int:id>/star")
@jwt_required()
def toggle_star(id: int):
    user = current_user()
    n = db.session.get(Notification, id)
    if not n or n.user_id != user.id:
        return jsonify({"error": "Not found"}), 404
    
    n.is_starred = not n.is_starred
    if not n.is_starred:
        # 💡 取消星标，重新开始 30 天计时
        from datetime import datetime, timedelta
        n.expires_at = datetime.utcnow() + timedelta(days=30)
    else:
        # 💡 加上星标，永不过期（或者设置一个极远的时间）
        n.expires_at = None
        
    db.session.commit()
    return jsonify({"success": True, "is_starred": n.is_starred})

@bp.delete("/<int:id>")
@jwt_required()
def delete_notification(id: int):
    user = current_user()
    n = db.session.get(Notification, id)
    if not n or n.user_id != user.id:
        return jsonify({"error": "Not found"}), 404
    
    db.session.delete(n)
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
