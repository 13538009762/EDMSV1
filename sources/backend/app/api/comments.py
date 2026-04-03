"""Document comments (batch on document versions)."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Comment, Document
from app.services.document_access import user_can_comment, user_can_view_document
from app.utils.auth import current_user

bp = Blueprint("comments_api", __name__)


def _serialize(c: Comment) -> dict:
    return {
        "id": c.id,
        "document_version_id": c.document_version_id,
        "author_id": c.author_id,
        "author_login": c.author.login_name if c.author else "",
        "body": c.body,
        "anchor_json": c.anchor_json,
        "status": c.status,
        "parent_id": c.parent_id,
        "hidden_when_resolved": c.hidden_when_resolved,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@bp.get("/documents/<int:doc_id>/comments")
@jwt_required()
def list_comments(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    ver = doc.current_version
    if not ver:
        return jsonify({"items": []})
    author_id = request.args.get("author_id", type=int)
    status = request.args.get("status")
    q = Comment.query.filter(Comment.document_version_id == ver.id)
    if author_id:
        q = q.filter(Comment.author_id == author_id)
    if status:
        q = q.filter(Comment.status == status)
    comments = q.order_by(Comment.created_at.asc()).all()
    hide_resolved = request.args.get("hide_resolved") == "1"
    items = []
    for c in comments:
        if hide_resolved and c.status == "resolved":
            continue
        items.append(_serialize(c))
    return jsonify({"items": items})


@bp.post("/documents/<int:doc_id>/comments")
@jwt_required()
def create_comment(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    if not user_can_comment(user, doc):
        return jsonify({"error": "Cannot comment on this document state"}), 403
    ver = doc.current_version
    if not ver:
        return jsonify({"error": "No version"}), 400
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    anchor = data.get("anchor_json")
    parent_id = data.get("parent_id")
    import json

    anchor_str = json.dumps(anchor) if isinstance(anchor, dict) else anchor
    c = Comment(
        document_version_id=ver.id,
        author_id=user.id,
        body=body,
        anchor_json=anchor_str,
        parent_id=parent_id,
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(_serialize(c)), 201


@bp.patch("/comments/<int:comment_id>")
@jwt_required()
def patch_comment(comment_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    c = db.session.get(Comment, comment_id)
    if not c:
        return jsonify({"error": "Not found"}), 404
    doc = c.document_version.document
    data = request.get_json(silent=True) or {}

    if "status" in data and data["status"] in ("active", "resolved"):
        # author can delete own - here resolve
        if c.author_id == user.id or doc.owner_id == user.id:
            c.status = data["status"]
    if "hidden_when_resolved" in data and (
        c.author_id == user.id or doc.owner_id == user.id
    ):
        c.hidden_when_resolved = bool(data["hidden_when_resolved"])

    if "delete" in data and data["delete"] and c.author_id == user.id:
        db.session.delete(c)
        db.session.commit()
        return jsonify({"ok": True})

    db.session.commit()
    return jsonify(_serialize(c))
