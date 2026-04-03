"""Approval inbox and decisions."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Document
from app.models.workflow import ApprovalFlow, ApprovalParticipant
from app.services.approval_service import apply_decision
from app.services.document_access import user_can_view_document
from app.utils.auth import current_user

bp = Blueprint("approvals", __name__)


@bp.get("/inbox")
@jwt_required()
def inbox():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    items = []
    flows = ApprovalFlow.query.filter_by(status="active").all()
    for flow in flows:
        doc = flow.document
        if not user_can_view_document(user, doc):
            continue
        for p in flow.participants:
            if p.user_id != user.id:
                continue
            if p.decision:
                continue
            if flow.flow_type == "sequential" and p.step_order != flow.current_order:
                continue
            total = len(flow.participants)
            done = sum(1 for x in flow.participants if x.decision)
            items.append(
                {
                    "participant_id": p.id,
                    "document_id": doc.id,
                    "title": doc.title,
                    "flow_type": flow.flow_type,
                    "progress": {"done": done, "total": total},
                    "current_order": flow.current_order,
                    "submitted_at": flow.created_at.isoformat() if flow.created_at else None,
                }
            )
    return jsonify({"items": items})


@bp.post("/participants/<int:participant_id>/decision")
@jwt_required()
def decide(participant_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    p = db.session.get(ApprovalParticipant, participant_id)
    if not p or p.user_id != user.id:
        return jsonify({"error": "Not found"}), 404
    doc = p.flow.document
    if not user_can_view_document(user, doc):
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json(silent=True) or {}
    decision = (data.get("decision") or "").lower()
    reason = data.get("reason")
    if decision not in ("approve", "reject"):
        return jsonify({"error": "decision must be approve or reject"}), 400
    if decision == "reject" and not (reason and str(reason).strip()):
        return jsonify({"error": "reason required for reject"}), 400
    try:
        apply_decision(p, decision, reason, doc)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    db.session.commit()
    return jsonify({"ok": True, "document_status": doc.status})
