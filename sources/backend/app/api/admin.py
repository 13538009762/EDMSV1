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

