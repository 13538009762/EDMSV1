from __future__ import annotations

from functools import wraps
from typing import Optional

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import User


def current_user() -> Optional[User]:
    uid = get_jwt_identity()
    if uid is None:
        return None
    try:
        iid = int(uid)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, iid)


def jwt_required_user(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "User not found"}), 401
        return fn(*args, **kwargs)

    return wrapper
