"""Admin endpoints for master data import (requires manager authentication)."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import verify_jwt_in_request

from app.extensions import db
from app.models import User
from app.services.import_xlsx import import_master_data_xlsx
from app.utils.auth import current_user

bp = Blueprint("admin", __name__)


def _has_managers() -> bool:
    return db.session.query(User.id).filter(User.is_manager == True).first() is not None


@bp.get("/status")
def admin_status():
    """Whether DB has managers (for UI hints)."""
    has_users = _has_managers()
    sample_managers = []
    if has_users:
        sample_managers = [
            u.login_name
            for u in db.session.query(User.login_name)
            .filter(User.is_manager == True)
            .limit(3)
            .all()
        ]
    return jsonify(
        {
            "has_users": has_users,
            "sample_managers": sample_managers,
        }
    )



@bp.post("/master-data/import")
def admin_import_master_data():
    """
    Import XLSX (clears documents and master data).
    If no managers exist: allow import without auth.
    If managers exist: require manager authentication.
    """
    # Check if there are any managers in the database
    has_managers = _has_managers()
    
    if has_managers:
        # Verify JWT token and check if user is a manager
        try:
            verify_jwt_in_request()
            user = current_user()
            if not user or not user.is_manager:
                return jsonify({
                    "error": "Authorization required. Please sign in as a manager to import master data."
                }), 403
        except Exception:
            return jsonify({
                "error": "Authorization required. Please sign in as a manager to import master data."
            }), 403
    # If no managers exist, allow import without authentication

    if "file" not in request.files:
        return jsonify({"error": "file required"}), 400
    f = request.files["file"]
    raw = f.read()
    if not raw:
        return jsonify({"error": "empty file"}), 400

    try:
        # We perform the import in a single transaction.
        # import_master_data_xlsx does NOT commit internally now.
        stats = import_master_data_xlsx(raw)
        db.session.commit()
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({"error": f"Import failed: {exc}"}), 400

    try:
        logins = [
            row[0]
            for row in db.session.query(User.login_name)
            .order_by(User.login_name)
            .limit(15)
            .all()
        ]
        stats["sample_login_names"] = logins
    except Exception:
        stats["sample_login_names"] = []

    return jsonify(stats), 200


from app.models.workflow import AuditLog
from flask_jwt_extended import jwt_required

@bp.get("/audit-logs")
@jwt_required()
def admin_list_audit_logs():
    """Get audit logs (System Admin only)"""
    user = current_user()
    if not user or user.login_name != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    query = AuditLog.query.filter(AuditLog.created_at >= cutoff)

    # Filters
    document_id = request.args.get("document_id")
    action = request.args.get("action")
    user_id = request.args.get("user_id")

    if document_id:
        query = query.filter(AuditLog.document_id == document_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 20))
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size).all()

    items = []
    for lg in logs:
        items.append({
            "id": lg.id,
            "document_id": lg.document_id,
            "document_title": lg.document.title if lg.document else None,
            "user_id": lg.user_id,
            "user_login": lg.user.login_name if lg.user else None,
            "action": lg.action,
            "summary": lg.summary,
            "ip_address": lg.ip_address,
            "created_at": lg.created_at.isoformat() + "Z" if lg.created_at else None
        })

    return jsonify({"total": total, "items": items})
