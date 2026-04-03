"""Master data XLSX import."""
from flask import Blueprint, current_app, jsonify, request

from app.services.import_xlsx import import_master_data_xlsx
from app.utils.auth import jwt_required_user

bp = Blueprint("master_data", __name__)


@bp.post("/import")
@jwt_required_user
def import_xlsx():
    """Import master data; requires JWT. If ADMIN_IMPORT_TOKEN is set, also require it in header X-Admin-Token."""
    admin = current_app.config.get("ADMIN_IMPORT_TOKEN") or ""
    if admin and request.headers.get("X-Admin-Token") != admin:
        return jsonify({"error": "Admin token required"}), 403

    if "file" not in request.files:
        return jsonify({"error": "file required"}), 400
    f = request.files["file"]
    raw = f.read()
    if not raw:
        return jsonify({"error": "empty file"}), 400
    try:
        stats = import_master_data_xlsx(raw)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400
    return jsonify(stats), 200
