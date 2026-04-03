from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required

from app.models import User
from app.utils.auth import current_user

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    """Login with login_name only (no password)."""
    data = request.get_json(silent=True) or {}
    login_name = (data.get("login_name") or "").strip()
    if not login_name:
        return jsonify({"error": "login_name required"}), 400
    user = User.query.filter_by(login_name=login_name).first()
    if not user:
        return jsonify({"error": "Invalid login"}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify(
        {
            "access_token": token,
            "user": {
                "id": user.id,
                "login_name": user.login_name,
                "display_name": user.display_name(),
                "is_manager": user.is_manager,
            },
        }
    )


@bp.get("/me")
@jwt_required()
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(
        {
            "id": user.id,
            "login_name": user.login_name,
            "display_name": user.display_name(),
            "is_manager": user.is_manager,
        }
    )
