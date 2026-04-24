"""Documents REST API."""
from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from sqlalchemy import or_, select

from app.models import (
    ApprovalFlow,
    Document,
    DocumentPermission,
    DocumentVersion,
    User,
)
from app.models.workflow import ApprovalParticipant, ApprovalDecision
from app.services.approval_service import start_flow
from app.services.diff_service import diff_html, blame_html, side_by_side_diff
from app.services.document_access import (
    user_can_comment,
    user_can_edit_content,
    user_can_edit_metadata,
    user_can_view_document,
    user_can_manage_permissions,
    user_effective_document_role,
)
from app.services.document_state import VALID_STATUSES
from app.services.export_service import export_docx_bytes, export_pdf_bytes
from app.utils.auth import current_user
from app.utils.audit import audit_log_required

bp = Blueprint("documents", __name__)


def _doc_to_summary(doc: Document, user: User) -> dict:
    ver = doc.current_version
    owner_name = None
    owner_department = None
    if doc.owner:
        owner_name = f"{doc.owner.last_name} {doc.owner.first_name}".strip()
        if doc.owner.department:
            owner_department = doc.owner.department.name
            owner_department_en = doc.owner.department.name_en
        else:
            owner_department_en = None
    # Check if current user is a pending approver for this document
    can_approve = False
    pending_participant_id = None
    if doc.status == "in_approval":
        flow = ApprovalFlow.query.filter_by(document_id=doc.id, status="active").first()
        if flow:
            # Find the participant for current user
            participant = ApprovalParticipant.query.filter_by(
                flow_id=flow.id, 
                user_id=user.id
            ).filter(ApprovalParticipant.id.not_in(
                select(ApprovalDecision.participant_id)
            )).first()
            
            if participant:
                # Also check if it's their turn for sequential
                if flow.flow_type == "parallel" or participant.step_order == flow.current_order:
                    can_approve = True
                    pending_participant_id = participant.id

    return {
        "id": doc.id,
        "doc_number": doc.doc_number or f"{doc.created_at.strftime('%Y%m%d') if doc.created_at else '00000000'}{str(doc.id).zfill(3)}",
        "title": doc.title,
        "status": doc.status,
        "owner_id": doc.owner_id,
        "owner_name": owner_name,
        "owner_department": owner_department,
        "owner_department_en": owner_department_en,
        "is_owner": doc.owner_id == user.id,
        "my_role": user_effective_document_role(user, doc),
        "created_at": doc.created_at.isoformat() + "Z" if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() + "Z" if doc.updated_at else None,
        "current_version_id": doc.current_version_id,
        "version_no": ver.version_no if ver else None,
        "can_view": True,
        "can_edit": user_can_edit_content(user, doc),
        "can_comment": user_can_comment(user, doc),
        "can_manage_permissions": user_can_manage_permissions(user, doc),
        "is_public": doc.is_public,
        "can_approve": can_approve,
        "pending_participant_id": pending_participant_id,
        "doc_type": doc.doc_type,
        "file_path": ver.file_path if ver else None,
    }

@bp.get("/tree")
@jwt_required()
def list_document_tree():
    """Return documents grouped by spaces in a hierarchical tree format."""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    from app.models.space import Space
    from app.models.core import Department
    
    spaces = Space.query.all()
    depts = Department.query.all()
    
    tree = []
    
    # 1. Spaces (Project/Topic Groups)
    for s in spaces:
        docs = Document.query.filter(
            Document.space_id == s.id,
            Document.is_template == False,
            Document.deleted_at == None,
            or_(
                Document.owner_id == user.id,
                Document.is_public == True
            )
        ).all()
        
        doc_map = {d.id: {
            "id": d.id,
            "title": d.title,
            "status": d.status,
            "parent_id": d.parent_id,
            "children": []
        } for d in docs}
        
        roots = []
        for d_id, d_data in doc_map.items():
            parent_id = d_data["parent_id"]
            if parent_id and parent_id in doc_map:
                doc_map[parent_id]["children"].append(d_data)
            else:
                roots.append(d_data)
                
        tree.append({
            "id": f"space_{s.id}",
            "space_id": s.id,
            "name": s.name,
            "is_space": True,
            "children": roots
        })

    # 2. Departments (Organizational Groups)
    for dpt in depts:
        # Show documents owned by users in this department that are NOT in a space
        # and are either public or owned by current user
        docs = Document.query.join(User).filter(
            User.department_id == dpt.id,
            Document.space_id == None,
            Document.is_template == False,
            Document.deleted_at == None,
            or_(
                Document.owner_id == user.id,
                Document.is_public == True
            )
        ).all()

        if not docs and dpt.id != user.department_id:
            continue

        doc_map = {d.id: {
            "id": d.id,
            "title": d.title,
            "status": d.status,
            "parent_id": d.parent_id,
            "children": []
        } for d in docs}
        
        roots = []
        for d_id, d_data in doc_map.items():
            parent_id = d_data["parent_id"]
            if parent_id and parent_id in doc_map:
                doc_map[parent_id]["children"].append(d_data)
            else:
                roots.append(d_data)

        tree.append({
            "id": f"dept_{dpt.id}",
            "name": dpt.name,
            "name_en": dpt.name_en,
            "is_dept": True,
            "is_space": True, # Use space icon for departments too
            "children": roots
        })
        
    orphan_docs = Document.query.filter(
        Document.space_id == None,
        Document.is_template == False,
        Document.deleted_at == None,
        Document.owner_id == user.id
    ).all()
    
    # Filter out docs already included in departments to avoid duplicates for the user
    # Actually, keep "Personal Documents" as a catch-all if needed, but usually dept is enough.
    
    return jsonify({"items": tree})

@bp.get("")
@jwt_required()
def list_documents():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    scope = request.args.get("scope")
    space_id = request.args.get("space_id")
    dept_id = request.args.get("dept_id")
    status_filter = request.args.get("status")
    on_chain = request.args.get("on_chain")

    if not scope:
        scope = "all"
    
    # Debug Probe
    print(f"[DEBUG] User {user.id} ({user.login_name}) listing docs with scope={scope}, space_id={space_id}")

    q = Document.query.filter(Document.is_template == False, Document.deleted_at == None)
    
    if on_chain == "true":
        q = q.filter(Document.tx_hash != None)
    
    # ── Admin Super Access ────────────────────────────────────────────────
    # If admin, show everything by default unless a specific space is filtered
    if user.login_name == 'admin' and scope == "all":
        pass 
    else:
        # Standard filtering for other users or specific scopes
        if status_filter:
            if status_filter not in VALID_STATUSES:
                return jsonify({"error": "invalid status filter"}), 400
            q = q.filter(Document.status == status_filter)

        if scope == "approved":
            q = q.filter(Document.status == "approved")
        elif scope == "collab":
            # 获取用户参与或有权限的 ID 列表
            perm_ids = [r[0] for r in db.session.query(DocumentPermission.document_id).filter_by(user_id=user.id).all()]
            flow_ids = [r[0] for r in db.session.query(ApprovalFlow.document_id)\
                       .join(ApprovalParticipant, ApprovalParticipant.flow_id == ApprovalFlow.id)\
                       .filter(ApprovalParticipant.user_id == user.id).all()]
            
            q = q.filter(
                or_(
                    Document.id.in_(perm_ids),
                    Document.id.in_(flow_ids),
                )
            ).filter(Document.owner_id != user.id)
        elif scope == "department":
            if user.department_id:
                dept_users = select(User.id).where(User.department_id == user.department_id)
                q = q.filter(Document.owner_id.in_(dept_users))
            else:
                q = q.filter(Document.id == -1)
        elif scope == "all":
            perm_ids = [r[0] for r in db.session.query(DocumentPermission.document_id).filter_by(user_id=user.id).all()]
            flow_ids = [r[0] for r in db.session.query(ApprovalFlow.document_id)\
                       .join(ApprovalParticipant, ApprovalParticipant.flow_id == ApprovalFlow.id)\
                       .filter(ApprovalParticipant.user_id == user.id).all()]
            
            q = q.filter(
                or_(
                    Document.owner_id == user.id,
                    Document.is_public == True,
                    Document.id.in_(perm_ids),
                    Document.id.in_(flow_ids),
                )
            )
        else:  # scope == "mine"
            q = q.filter(Document.owner_id == user.id)

    # Re-apply space filter at the end
    if space_id:
        if space_id == "unassigned":
            q = q.filter(Document.space_id == None)
        else:
            q = q.filter(Document.space_id == space_id)

    if dept_id:
        q = q.join(User).filter(User.department_id == dept_id, Document.space_id == None)

    docs = q.order_by(Document.updated_at.desc()).all()
    print(f"[DEBUG] Query found {len(docs)} documents")
    return jsonify({"items": [_doc_to_summary(d, user) for d in docs]})


@bp.post("")
@jwt_required()
def create_document():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Untitled").strip()[:512]
    space_id = data.get("space_id")
    
    # Generate doc_number (resets daily)
    from sqlalchemy import func
    # 使用本地时间而非 UTC，确保编号符合用户直觉日期
    today_str = datetime.now().strftime("%Y%m%d")
    # 查找当天最高编号以确保跨天重置且不因删除导致编号冲突
    max_doc = db.session.query(func.max(Document.doc_number)).filter(
        Document.doc_number.like(f"{today_str}%")
    ).scalar()
    if max_doc:
        try:
            last_seq = int(max_doc[-3:])
            doc_number = f"{today_str}{str(last_seq + 1).zfill(3)}"
        except:
            doc_number = f"{today_str}001"
    else:
        doc_number = f"{today_str}001"
    
    try:
        doc = Document(owner_id=user.id, title=title, status="draft", doc_number=doc_number, space_id=space_id)
        db.session.add(doc)
        db.session.flush()
        ver = DocumentVersion(
            document_id=doc.id,
            version_no=1,
            content_json=DocumentVersion.default_content_json(),
            created_by_id=user.id,
        )
        db.session.add(ver)
        db.session.flush()
        doc.current_version_id = ver.id
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create document: {str(e)}"}), 500
        
    return jsonify(_doc_to_summary(doc, user)), 201


@bp.post("/import-pdf")
@jwt_required()
def import_pdf():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    title = request.form.get("title") or file.filename
    space_id = request.form.get("space_id")
    
    # Save file
    filename = f"{uuid.uuid4()}.pdf"
    # Ensure directory exists in workspace
    upload_dir = os.path.join("app", "static", "uploads", "pdfs")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    
    dest_path = os.path.join(upload_dir, filename)
    file.save(dest_path)
    
    # Relative URL for frontend
    relative_path = f"/static/uploads/pdfs/{filename}"
    
    # Generate doc_number
    from sqlalchemy import func
    today_str = datetime.now().strftime("%Y%m%d")
    max_doc = db.session.query(func.max(Document.doc_number)).filter(
        Document.doc_number.like(f"{today_str}%")
    ).scalar()
    if max_doc:
        try:
            last_seq = int(max_doc[-3:])
            doc_number = f"{today_str}{str(last_seq + 1).zfill(3)}"
        except:
            doc_number = f"{today_str}001"
    else:
        doc_number = f"{today_str}001"
        
    doc = Document(
        owner_id=user.id, 
        title=title, 
        status="draft", 
        doc_number=doc_number, 
        space_id=space_id if space_id and space_id != "unassigned" else None,
        doc_type="pdf"
    )
    db.session.add(doc)
    db.session.flush()
    
    ver = DocumentVersion(
        document_id=doc.id,
        version_no=1,
        file_path=relative_path,
        created_by_id=user.id,
    )
    db.session.add(ver)
    db.session.flush()
    doc.current_version_id = ver.id
    db.session.commit()
    
    return jsonify(_doc_to_summary(doc, user)), 201


@bp.get("/<int:doc_id>")
@jwt_required()
@audit_log_required("VIEW")
def get_document(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    ver = doc.current_version
    body = {
        **_doc_to_summary(doc, user),
        "owner_login": doc.owner.login_name if doc.owner else None,
        "page_settings_json": doc.page_settings_json,
        "content_json": ver.content_json if ver else None,
        "yjs_state_b64": base64.b64encode(ver.yjs_state).decode("ascii")
        if ver and ver.yjs_state
        else None,
        "file_path": ver.file_path if ver else None,
        "doc_type": doc.doc_type,
    }
    return jsonify(body)


@bp.patch("/<int:doc_id>")
@jwt_required()
def patch_document(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(silent=True) or {}
    if "title" in data:
        if not user_can_edit_metadata(user, doc):
            return jsonify({"error": "Forbidden: cannot edit title in current state/role"}), 403
        doc.title = str(data["title"])[:512]
    if "page_settings_json" in data:
        doc.page_settings_json = data["page_settings_json"]
    if "is_public" in data:
        if not user_can_manage_permissions(user, doc):
            return jsonify({"error": "Forbidden: only owner or approver (after approval) can change visibility"}), 403
        doc.is_public = bool(data["is_public"])
    doc.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_doc_to_summary(doc, user))


@bp.put("/<int:doc_id>/content")
@jwt_required()
def put_content(doc_id: int):
    """Autosave document body (TipTap JSON + optional Yjs state)."""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    if not user_can_edit_content(user, doc):
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json(silent=True) or {}
    ver = doc.current_version
    if not ver:
        return jsonify({"error": "No version"}), 400

    from datetime import timedelta
    # Create new version if user changed OR 5+ minutes passed since last version creation
    time_passed = (datetime.utcnow() - ver.created_at) > timedelta(minutes=5)
    if (ver.created_by_id != user.id) or time_passed:
        new_ver = DocumentVersion(
            document_id=doc.id,
            version_no=ver.version_no + 1,
            parent_version_id=ver.id,
            created_by_id=user.id,
            content_json=ver.content_json,
            yjs_state=ver.yjs_state,
        )
        db.session.add(new_ver)
        db.session.flush()
        doc.current_version_id = new_ver.id
        ver = new_ver

    if "content_json" in data:
        cj = data["content_json"]
        ver.content_json = json.dumps(cj) if isinstance(cj, (dict, list)) else str(cj)
    if "yjs_state_b64" in data and data["yjs_state_b64"]:
        ver.yjs_state = base64.b64decode(data["yjs_state_b64"])
    
    doc.updated_at = datetime.utcnow()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Autosave failed: {str(e)}"}), 500
        
    return jsonify({"ok": True})


@bp.delete("/<int:doc_id>")
@jwt_required()
@audit_log_required("DELETE")
def delete_document(doc_id: int):
    """Delete a draft or rejected document (only owner)."""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({"error": "Not found"}), 404
    
    # Only owner
    if doc.owner_id != user.id:
        return jsonify({"error": "Forbidden: Only creator can delete"}), 403
    
    # Only draft, approved or rejected (basically not in_approval)
    if doc.status not in ("draft", "approved", "rejected"):
        return jsonify({"error": f"Forbidden: Cannot delete document in status {doc.status}"}), 400
    
    # Manually clear AuditLog references to prevent FK issues in environments with enforced constraints
    from app.models.workflow import AuditLog
    v_ids = [v.id for v in doc.versions]
    if v_ids:
        db.session.query(AuditLog).filter(AuditLog.document_version_id.in_(v_ids)).update(
            {AuditLog.document_version_id: None}, synchronize_session=False
        )

    db.session.delete(doc)
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/<int:doc_id>/versions")
@jwt_required()
def list_versions(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    items = []
    # Sort by version_no desc for latest first
    for v in sorted(doc.versions, key=lambda x: x.version_no, reverse=True):
        items.append(
            {
                "id": v.id,
                "version_no": v.version_no,
                "created_at": v.created_at.isoformat() + "Z" if v.created_at else None,
                "parent_version_id": v.parent_version_id,
                "created_by_id": v.created_by_id,
                "created_by_name": v.created_by.login_name if v.created_by else "System",
            }
        )
    return jsonify({"items": items})


@bp.get("/<int:doc_id>/versions/<int:vid>/content")
@jwt_required()
def get_version_content(doc_id: int, vid: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    v = db.session.get(DocumentVersion, vid)
    if not v or v.document_id != doc.id:
        return jsonify({"error": "Not found"}), 404
    return jsonify(
        {
            "content_json": v.content_json,
            "version_no": v.version_no,
        }
    )


@bp.get("/<int:doc_id>/diff")
@jwt_required()
def get_diff(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    v_from = request.args.get("from", type=int)
    v_to = request.args.get("to", type=int)
    if not v_from or not v_to:
        return jsonify({"error": "from and to version ids required"}), 400
    a = db.session.get(DocumentVersion, v_from)
    b = db.session.get(DocumentVersion, v_to)
    if not a or not b or a.document_id != doc.id or b.document_id != doc.id:
        return jsonify({"error": "Invalid versions"}), 400
    mode = request.args.get("mode", "inline")
    if mode == "side_by_side":
        html_data = side_by_side_diff(a.content_json or "{}", b.content_json or "{}")
    else:
        html_data = diff_html(a.content_json or "{}", b.content_json or "{}")
    return jsonify({"html": html_data})


@bp.get("/<int:doc_id>/blame")
@jwt_required()
def get_blame(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
        
    versions_data = []
    colors = ["#f87171", "#fb923c", "#fbbf24", "#34d399", "#38bdf8", "#818cf8", "#c084fc", "#f472b6"]
    author_color_map = {}
    
    for v in sorted(doc.versions, key=lambda x: x.version_no):
        author_name = "Unknown"
        if v.created_by:
            author_name = f"{v.created_by.last_name} {v.created_by.first_name}".strip() or v.created_by.login_name
            
        if author_name not in author_color_map:
            author_color_map[author_name] = colors[len(author_color_map) % len(colors)]
            
        versions_data.append({
            "version_no": v.version_no,
            "content_json": v.content_json,
            "author_name": author_name,
            "author_color": author_color_map[author_name],
            "created_at": v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else ""
        })
        
    html_out = blame_html(versions_data)
    legend = [{"name": k, "color": v} for k, v in author_color_map.items()]
    
    return jsonify({"html": html_out, "legend": legend})


@bp.post("/<int:doc_id>/permissions")
@jwt_required()
def set_permissions(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_manage_permissions(user, doc):
        return jsonify({"error": "Forbidden"}), 403
    if doc.status not in ("draft", "approved"):
        return jsonify({"error": "Permissions can only be changed while document is draft or approved"}), 400
    data = request.get_json(silent=True) or {}
    grants = data.get("grants") or []
    seen: set[int] = set()
    DocumentPermission.query.filter_by(document_id=doc.id).delete()
    for g in grants:
        uid = g.get("user_id")
        role = g.get("role")
        if doc.status == "approved" and role not in ("view", "comment"):
            continue # 已审批通过只能改查看和批注
        if doc.status == "draft" and role not in ("view", "edit", "comment"):
            # 草稿允许编辑和评论
            continue
        if not uid:
            continue
        uid_int = int(uid)
        if uid_int == user.id:
            continue
        if uid_int in seen:
            continue
        seen.add(uid_int)
        if not db.session.get(User, uid_int):
            return jsonify({"error": f"Unknown user_id: {uid_int}"}), 400
        db.session.add(
            DocumentPermission(document_id=doc.id, user_id=uid_int, role=role),
        )

        # 💡 处理通知逻辑
        should_notify = (role == "edit") or (data.get("notify") is True)
        if should_notify:
            from app.models.notification import Notification
            from datetime import datetime, timedelta
            
            # 检查是否已有相同文档的未读协作通知，避免刷屏
            existing = Notification.query.filter_by(
                user_id=uid_int, 
                related_doc_id=doc.id, 
                type="协作", 
                is_read=False
            ).first()
            
            if not existing:
                title = f"待编辑: {doc.title}" if role == "edit" else f"共享文档: {doc.title}"
                expires = datetime.utcnow() + timedelta(days=30) if role == "edit" else None
                
                # 💡 增加过期时间 30 天
                from datetime import datetime, timedelta
                expires = datetime.utcnow() + timedelta(days=30)
                
                print(f"[DEBUG] Creating share notification for user {uid_int}, doc {doc.id}")
                new_notif = Notification(
                    user_id=uid_int,
                    type="协作",
                    title=title,
                    content=f"用户 {user.display_name()} 为您分配了文档的 {role} 权限。",
                    related_doc_id=doc.id,
                    link_url=f"/doc/{doc.id}",
                    expires_at=expires
                )
                db.session.add(new_notif)

    print(f"[DEBUG] Committing permissions for doc {doc.id}")
    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/<int:doc_id>/permissions/<int:grantee_id>")
@jwt_required()
def delete_permission(doc_id: int, grantee_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_manage_permissions(user, doc):
        return jsonify({"error": "Forbidden"}), 403
    if doc.status not in ("draft", "approved"):
        return jsonify({"error": "Permissions can only be changed while document is draft or approved"}), 400
    p = DocumentPermission.query.filter_by(
        document_id=doc.id, user_id=grantee_id
    ).first()
    if not p:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/<int:doc_id>/permissions")
@jwt_required()
def get_permissions(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_manage_permissions(user, doc):
        return jsonify({"error": "Not found"}), 404
    perms = DocumentPermission.query.filter_by(document_id=doc.id).all()
    return jsonify(
        {
            "items": [
                {"user_id": p.user_id, "role": p.role, "login_name": p.user.login_name}
                for p in perms
            ]
        }
    )


@bp.get("/<int:doc_id>/collaborators")
@jwt_required()
def get_collaborators(doc_id: int):
    """获取文档的协作者列表（当前有权限的用户）"""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    
    # 获取有权限的用户（包括 owner 和有权限的用户）
    collabs = []
    # 添加 owner
    if doc.owner:
        collabs.append({
            "user_id": doc.owner.id,
            "login_name": doc.owner.login_name,
            "name": doc.owner.display_name(),
            "is_owner": True
        })
    
    # 获取有权限的用户
    perms = DocumentPermission.query.filter_by(document_id=doc.id).all()
    for p in perms:
        if p.user:
            collabs.append({
                "user_id": p.user.id,
                "login_name": p.user.login_name,
                "name": p.user.display_name(),
                "role": p.role,
                "is_owner": False
            })
    
    return jsonify({"items": collabs})


@bp.get("/<int:doc_id>/export.docx")
@jwt_required()
@audit_log_required("EXPORT_DOCX")
def export_docx(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    ver = doc.current_version
    ps = json.loads(doc.page_settings_json) if doc.page_settings_json else None
    raw = export_docx_bytes(ver.content_json if ver else "{}", page_settings=ps)
    return Response(
        raw,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="doc_{doc_id}.docx"'},
    )


@bp.get("/<int:doc_id>/export.pdf")
@jwt_required()
@audit_log_required("EXPORT_PDF")
def export_pdf(doc_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_view_document(user, doc):
        return jsonify({"error": "Not found"}), 404
    ver = doc.current_version
    ps = json.loads(doc.page_settings_json) if doc.page_settings_json else None
    
    watermark_text = f"{user.display_name()} · {user.employee_no} · {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    raw = export_pdf_bytes(ver.content_json if ver else "{}", page_settings=ps, watermark_text=watermark_text)
    return Response(
        raw,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="doc_{doc_id}.pdf"'},
    )


@bp.post("/upload-image")
@jwt_required()
def upload_image():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if "file" not in request.files:
        return jsonify({"error": "No file parameter"}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected"}), 400
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return jsonify({"error": "Invalid image extension. Only jpg, png, gif, webp allowed."}), 400
        
    from flask import current_app
    # 💡 优化：从环境变量获取存储路径，方便 Docker 持久化
    storage_base = os.environ.get("STORAGE_PATH", current_app.root_path)
    save_dir = os.path.join(storage_base, "static", "images")
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    
    file.save(os.path.join(save_dir, filename))
    # 注意：URL 仍然通过 /static/images 访问，我们需要在 Web 服务器配置静态映射
    url = f"/static/images/{filename}"
    return jsonify({"url": url})



@bp.post("/<int:doc_id>/approvals")
@jwt_required()
def start_approval(doc_id: int):
    user = current_user()
    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
        
    print(f"[DEBUG] Starting approval for doc {doc_id} by user {user.login_name if user else 'UNKNOWN'}. Doc Owner: {doc.owner_id}, Status: {doc.status}")
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # 💡 只有草稿状态才能发起审批
    if doc.status != "draft":
        return jsonify({"error": f"Cannot start approval: Document is already in {doc.status} status."}), 400
        
    if not user_can_manage_permissions(user, doc):
        return jsonify({"error": "Forbidden: You don't have permission to start approval for this document."}), 403
    
    data = request.get_json(silent=True) or {}
    flow_type = (data.get("type") or "parallel").lower()
    ids = data.get("approvers") or []
    print(f"[DEBUG] Flow type: {flow_type}, Approver IDs: {ids}")
    
    if flow_type not in ("parallel", "sequential"):
        return jsonify({"error": "invalid flow_type"}), 400
    approvers = [int(x) for x in ids]
    
    if doc.owner_id in approvers:
        return jsonify({"error": "Owner cannot be an approver"}), 400
        
    try:
        from app.services.approval_service import start_flow
        from app.extensions import socketio
        from app.models.notification import Notification

        # 1. 核心流程：创建审批流
        flow = start_flow(doc, flow_type, approvers)
        
        # 2. 发送通知给审批人
        sender_name = user.display_name()
        for aud in approvers:
            n = Notification(
                user_id=aud,
                type="审批",
                title=f"待审批: {doc.title}",
                content=f"用户 {sender_name} 邀请您审批文档 '{doc.title}'。",
                related_doc_id=doc_id,
                link_url=f"/inbox"
            )
            db.session.add(n)
        
        db.session.commit()
        print(f"[DEBUG] Transaction committed. Flow: {flow.id}")

        # 3. 实时通知前端（💡 关键修复：扔进后台任务，绝不阻塞当前请求）
        socketio.start_background_task(
            socketio.emit,
            "status_change",
            {
                "document_id": doc_id,
                "status": doc.status,
                "can_edit": False
            },
            room=f"doc_{doc_id}"
        )
        
        return jsonify({
            "flow_id": flow.id, 
            "document_status": doc.status,
            "can_edit": False
        })
    except Exception as e:
        db.session.rollback()
        print(f"[DEBUG] ERROR in start_approval: {str(e)}")
        return jsonify({"error": str(e)}), 400


@bp.post("/<int:doc_id>/recall")
@jwt_required()
def recall_document_approval(doc_id: int):
    """Recall a document from approval state."""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or doc.owner_id != user.id:
        return jsonify({"error": "Forbidden"}), 403
    
    from app.services.approval_service import recall_flow
    try:
        recall_flow(doc)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
        
    db.session.commit()

    # 💡 使用后台任务发送实时状态通知，不阻塞响应
    from app.extensions import socketio
    socketio.start_background_task(
        socketio.emit,
        "status_change",
        {
            "document_id": doc.id,
            "status": doc.status,
            "can_edit": True
        },
        room=f"doc_{doc.id}"
    )

    return jsonify({"ok": True, "document_status": doc.status})


@bp.post("/<int:doc_id>/new-version")
@jwt_required()
def new_version_after_reject(doc_id: int):
    """Create new version from current content when document was rejected."""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc or not user_can_manage_permissions(user, doc):
        return jsonify({"error": "Forbidden"}), 403
    if doc.status != "rejected":
        return jsonify({"error": "Only rejected documents"}), 400
    old = doc.current_version
    max_no = max((v.version_no for v in doc.versions), default=0)
    ver = DocumentVersion(
        document_id=doc.id,
        version_no=max_no + 1,
        content_json=old.content_json if old else DocumentVersion.default_content_json(),
        yjs_state=old.yjs_state if old else None,
        created_by_id=user.id,
        parent_version_id=old.id if old else None,
    )
    db.session.add(ver)
    db.session.flush()
    doc.current_version_id = ver.id
    doc.status = "draft"
    doc.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"current_version_id": ver.id, "version_no": ver.version_no})

@bp.post("/batch-delete")
@jwt_required()
def batch_delete_documents():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    doc_ids = data.get("doc_ids", [])
    
    success_count = 0
    errors = []
    
    from app.models.workflow import AuditLog
    
    for did in doc_ids:
        doc = db.session.get(Document, did)
        if not doc:
            continue
        
        # Permission check
        if doc.owner_id != user.id:
            errors.append(f"Doc {did}: Forbidden")
            continue
        if doc.status not in ("draft", "rejected"):
            errors.append(f"Doc {did}: Cannot delete in status {doc.status}")
            continue
            
        # Success path
        v_ids = [v.id for v in doc.versions]
        if v_ids:
            db.session.query(AuditLog).filter(AuditLog.document_version_id.in_(v_ids)).update(
                {AuditLog.document_version_id: None}, synchronize_session=False
            )
        db.session.delete(doc)
        success_count += 1
        
    db.session.commit()
    return jsonify({"message": f"Deleted {success_count} documents", "errors": errors})

@bp.post("/batch-share")
@jwt_required()
def batch_share_documents():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    doc_ids = data.get("doc_ids", [])
    is_public = data.get("is_public", False)
    
    success_count = 0
    errors = []
    
    for did in doc_ids:
        doc = db.session.get(Document, did)
        if not doc:
            continue
        
        if not user_can_manage_permissions(user, doc):
            errors.append(f"Doc {did}: Forbidden")
            continue
            
        doc.is_public = is_public
        success_count += 1
        
    db.session.commit()
    return jsonify({"message": f"Shared {success_count} documents", "errors": errors})

@bp.route('/<int:doc_id>/archive', methods=['POST'])
@jwt_required()
def archive_document(doc_id):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({"error": "Not found"}), 404
        
    from app.services.mock_blockchain import MockBlockchainService
    current_version = doc.current_version
    
    # 1. 算哈希
    doc_hash = MockBlockchainService.calculate_hash(current_version.content_json if current_version else '')
    
    # 2. 模拟上链
    tx_hash = MockBlockchainService.mock_notarize_to_chain()
    
    # 3. 固化凭证到 documents 主表
    doc.status = 'approved' 
    doc.file_hash = doc_hash
    doc.tx_hash = tx_hash
    db.session.commit()
    
    return jsonify({"msg": "归档并上链成功", "tx_hash": tx_hash})

@bp.route('/<int:doc_id>/verify', methods=['GET'])
@jwt_required()
def verify_document(doc_id):
    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({"error": "Not found"}), 404
        
    from app.services.mock_blockchain import MockBlockchainService
    import time
    
    current_version = doc.current_version
    
    # 重新计算当前数据库里文本的哈希
    current_hash = MockBlockchainService.calculate_hash(current_version.content_json if current_version else '')
    
    time.sleep(0.8) # 模拟正在全网广播查询的延迟
    
    # 核心拦截逻辑：拿现在的哈希 vs 归档时存的哈希
    if current_hash == doc.file_hash:
        return jsonify({
            "safe": True, 
            "msg": "链上指纹匹配，数据未被篡改！", 
            "tx_hash": doc.tx_hash
        })
    else:
        # ======= 新增：真正把内鬼行为写入数据库 =======
        from app.models.workflow import AuditLog
        from flask import request
        user = current_user()
        
        tamper_log = AuditLog(
            user_id=user.id if user else None,
            document_id=doc.id,             
            action='ALERT_TAMPER',          
            ip_address=request.remote_addr, 
            summary='【零信任拦截】用户发起确权审计，系统比对发现底层物理数据已被未知来源非法篡改，已阻断！' 
        )
        db.session.add(tamper_log)
        db.session.commit()
        # ===============================================
        return jsonify({
            "safe": False, 
            "msg": "致命警告：底层数据哈希异常，文件已遭非法篡改！"
        })
