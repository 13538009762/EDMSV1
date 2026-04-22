"""Approval inbox and decisions."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.core import User, Department
from app.models.document import Document
from app.models.workflow import ApprovalFlow, ApprovalParticipant
from app.services.approval_service import apply_decision
from app.services.document_access import user_can_view_document
from sqlalchemy import text
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
        if flow.flow_type == "registration":
            # Admin or Manager of the appropriate dept can see it
            # Already checked by participants filter below, but good to have a title
            title = f"User Registration: {User.query.get(flow.rel_id).display_name() if flow.rel_id else 'New User'}"
        elif doc:
            if not user_can_view_document(user, doc):
                continue
            title = doc.title
        else:
            continue

        for p in flow.participants:
            # NORMAL FILTER: only show if it is MY turn
            is_my_turn = p.user_id == user.id and not p.decision
            if flow.flow_type == "sequential" and p.step_order != flow.current_order:
                is_my_turn = False
            
            # ADMIN OVERRIDE: admin can see and handle ANY registration flow active step
            force_show = (user.login_name == 'admin' and flow.flow_type == "registration" and p.step_order == flow.current_order)
            
            if not is_my_turn and not force_show:
                continue
            participants = []
            for p_detail in flow.participants:
                user_name = f"{p_detail.user.last_name} {p_detail.user.first_name}".strip() if p_detail.user else "Unknown"
                participants.append({
                    "user_id": p_detail.user_id,
                    "user_name": user_name,
                    "decision": p_detail.decision.decision if p_detail.decision else None,
                    "reason": p_detail.decision.reason if p_detail.decision else None,
                    "step_order": p_detail.step_order
                })

            total = len(flow.participants)
            done = sum(1 for x in flow.participants if x.decision)
            items.append(
                {
                    "participant_id": p.id,
                    "document_id": doc.id if doc else None,
                    "title": title,
                    "flow_status": flow.status,
                    "flow_type": flow.flow_type,
                    "progress": {"done": done, "total": total},
                    "current_order": flow.current_order,
                    "submitted_at": flow.created_at.isoformat() + "Z" if flow.created_at else None,
                    "details": participants,
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
    if not p:
        return jsonify({"error": "Not found"}), 404
    
    # Check if this flow is for the current user OR if current user is admin manually taking over a registration
    is_admin_override = (user.login_name == 'admin' and p.flow.flow_type == 'registration')
    if p.user_id != user.id and not is_admin_override:
         return jsonify({"error": "Forbidden"}), 403
    doc = p.flow.document
    if doc and not user_can_view_document(user, doc):
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

    # 💡 如果文档审批完成（通过），执行上链存证并通知所有编辑者
    if doc and doc.status == "approved":
        # === 零信任区块链确权：自动化防篡改上链 ===
        from app.services.mock_blockchain import MockBlockchainService
        from app.models.document import DocumentVersion
        
        current_version = DocumentVersion.query.get(doc.current_version_id)
        if current_version:
            # 1. 算哈希
            doc_hash = MockBlockchainService.calculate_hash(current_version.content_json)
            # 2. 模拟上链
            tx_hash = MockBlockchainService.mock_notarize_to_chain()
            # 3. 固化凭证
            doc.file_hash = doc_hash
            doc.tx_hash = tx_hash
            db.session.commit()
            print(f"[Blockchain] Notarized Document {doc.id} with tx: {tx_hash}")

        from app.models.notification import Notification
        members_to_notify = []
        # 文署的所有者
        if doc.owner_id: members_to_notify.append(doc.owner_id)
        # 文署的所有权限持有者（编辑者/评论者）
        from app.models.document import DocumentPermission
        perms = DocumentPermission.query.filter_by(document_id=doc.id).all()
        for perm in perms:
            if perm.user_id not in members_to_notify:
                members_to_notify.append(perm.user_id)
        
        for mid in members_to_notify:
            # 不通知合规审计（如果有）、不通知自己（当前审批完结人）
            if mid == user.id: continue
            
            n = Notification(
                user_id=mid,
                type="系统",
                title=f"文档已批准: {doc.title}",
                content=f"您参与的文档 '{doc.title}' 已经通过审批。",
                related_doc_id=doc.id,
                link_url=f"/doc/{doc.id}"
            )
            db.session.add(n)
        db.session.commit()

    if doc:
        from app.extensions import socketio
        socketio.emit("status_change", {
            "document_id": doc.id,
            "status": doc.status,
            "can_edit": (doc.status in ("draft", "approved"))
        }, room=f"doc_{doc.id}")

    return jsonify({"ok": True, "document_status": doc.status if doc else "N/A"})


@bp.get("/my-applications")
@jwt_required()
def my_applications():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # 获取我提交的所有文档的审批流（包括已完成、已驳回和撤销的）
    from app.models import Document
    from app.models.workflow import ApprovalFlow
    
    # 获取我拥有的所有文档的所有审批流（排除已撤销的），按时间倒序
    flows = ApprovalFlow.query.join(Document).filter(
        Document.owner_id == user.id,
        ApprovalFlow.status != 'cancelled'
    ).order_by(ApprovalFlow.created_at.desc()).all()
    
    items = []
    for flow in flows:
        doc = flow.document
        participants = []
        for p in flow.participants:
            user_name = f"{p.user.last_name} {p.user.first_name}".strip() if p.user else "Unknown"
            participants.append({
                "user_id": p.user_id,
                "user_name": user_name,
                "decision": p.decision.decision if p.decision else None,
                "reason": p.decision.reason if p.decision else None,
                "step_order": p.step_order
            })
            
        items.append({
            "document_id": doc.id,
            "title": doc.title,
            "flow_id": flow.id,
            "flow_type": flow.flow_type,
            "flow_status": flow.status,
            "progress": {"done": sum(1 for x in flow.participants if x.decision), "total": len(flow.participants)},
            "submitted_at": flow.created_at.isoformat() + "Z" if flow.created_at else None,
            "details": participants
        })
        
    return jsonify({"items": items})
