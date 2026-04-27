"""Template Gallery API — admin management & public listing."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.document import Document, DocumentVersion
from app.utils.auth import current_user
from datetime import datetime

bp = Blueprint("templates", __name__)


def _can_manage_templates(user) -> bool:
    return user is not None and (user.login_name == "admin" or user.is_manager)


def _is_super_admin(user) -> bool:
    return user is not None and user.login_name == "admin"


# ──────────────────────────────────────────────────────────────
#  PUBLIC — all authenticated employees can view published templates
# ──────────────────────────────────────────────────────────────
@bp.get("")
@jwt_required()
def list_templates():
    """List all published templates (is_template=True, is_public=True)."""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    templates = (
        Document.query
        .filter_by(is_template=True, is_public=True, deleted_at=None)
        .order_by(Document.updated_at.desc())
        .all()
    )
    items = []
    for t in templates:
        items.append({
            "id": t.id,
            "title": t.title,
            "description": t.template_description or "",
            "icon": t.template_icon or "Document",
            "created_at": t.created_at.isoformat() + "Z" if t.created_at else None,
            "updated_at": t.updated_at.isoformat() + "Z" if t.updated_at else None,
            "owner_name": t.owner.display_name() if t.owner else "System",
        })
    return jsonify({"items": items})


@bp.post("/<int:tmpl_id>/create-from")
@jwt_required()
def clone_from_template(tmpl_id: int):
    """Create a new draft document from a published template."""
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    tmpl = db.session.get(Document, tmpl_id)
    if not tmpl or not tmpl.is_template or not tmpl.is_public:
        return jsonify({"error": "Template not found"}), 404

    from sqlalchemy import func
    today_str = datetime.utcnow().strftime("%Y%m%d")
    max_doc = db.session.query(func.max(Document.doc_number)).filter(
        Document.doc_number.like(f"{today_str}%")
    ).scalar()
    if max_doc:
        try:
            last_seq = int(max_doc[-3:])
            doc_number = f"{today_str}{str(last_seq + 1).zfill(3)}"
        except Exception:
            doc_number = f"{today_str}001"
    else:
        doc_number = f"{today_str}001"

    doc = Document(
        owner_id=user.id,
        title=f"New from {tmpl.title}",
        status="draft",
        doc_number=doc_number
    )
    db.session.add(doc)
    db.session.flush()

    tmpl_ver = tmpl.current_version
    content_json = tmpl_ver.content_json if tmpl_ver else DocumentVersion.default_content_json()

    ver = DocumentVersion(
        document_id=doc.id,
        version_no=1,
        content_json=content_json,
        created_by_id=user.id,
    )
    db.session.add(ver)
    db.session.flush()
    doc.current_version_id = ver.id

    if tmpl.page_settings_json:
        doc.page_settings_json = tmpl.page_settings_json

    db.session.commit()
    return jsonify({"id": doc.id, "title": doc.title}), 201


# ──────────────────────────────────────────────────────────────
#  ADMIN — full management of templates
# ──────────────────────────────────────────────────────────────
@bp.get("/admin")
@jwt_required()
def admin_list_templates():
    """Admin/Manager: list relevant templates."""
    user = current_user()
    if not _can_manage_templates(user):
        return jsonify({"error": "Forbidden"}), 403

    # Managers now see ALL templates, but can't operate on others'
    templates = Document.query.filter_by(is_template=True, deleted_at=None).order_by(Document.updated_at.desc()).all()
    items = []
    for t in templates:
        items.append({
            "id": t.id,
            "title": t.title,
            "description": t.template_description or "",
            "icon": t.template_icon or "Document",
            "is_public": t.is_public,
            "created_at": t.created_at.isoformat() + "Z" if t.created_at else None,
            "updated_at": t.updated_at.isoformat() + "Z" if t.updated_at else None,
            "owner_name": t.owner.display_name() if t.owner else "System",
            "owner_id": t.owner_id,
        })
    return jsonify({"items": items})


@bp.post("/admin")
@jwt_required()
def admin_create_template():
    """Admin/Manager: create a new template."""
    user = current_user()
    if not _can_manage_templates(user):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Untitled Template").strip()[:512]
    description = (data.get("description") or "").strip()[:512]
    is_public = bool(data.get("is_public", False))

    from sqlalchemy import func
    today_str = datetime.utcnow().strftime("%Y%m%d")
    max_doc = db.session.query(func.max(Document.doc_number)).filter(
        Document.doc_number.like(f"{today_str}%")
    ).scalar()
    if max_doc:
        try:
            last_seq = int(max_doc[-3:])
            doc_number = f"{today_str}{str(last_seq + 1).zfill(3)}"
        except Exception:
            doc_number = f"{today_str}001"
    else:
        doc_number = f"{today_str}001"

    tmpl = Document(
        owner_id=user.id,
        title=title,
        template_description=description,
        template_icon=data.get("icon", "Document"),
        status="draft",   # Templates start as draft so they can be edited
        is_template=True,
        is_public=is_public,
        doc_number=doc_number,
    )
    db.session.add(tmpl)
    db.session.flush()

    ver = DocumentVersion(
        document_id=tmpl.id,
        version_no=1,
        content_json=DocumentVersion.default_content_json(),
        created_by_id=user.id,
    )
    db.session.add(ver)
    db.session.flush()
    tmpl.current_version_id = ver.id

    db.session.commit()
    return jsonify({
        "id": tmpl.id,
        "title": tmpl.title,
        "description": tmpl.template_description or "",
        "icon": tmpl.template_icon or "Document",
        "is_public": tmpl.is_public,
    }), 201


@bp.patch("/admin/<int:tmpl_id>")
@jwt_required()
def admin_update_template(tmpl_id: int):
    """Admin/Manager: update template metadata."""
    user = current_user()
    if not _can_manage_templates(user):
        return jsonify({"error": "Forbidden"}), 403

    tmpl = db.session.get(Document, tmpl_id)
    if not tmpl or not tmpl.is_template:
        return jsonify({"error": "Template not found"}), 404
        
    # Ownership check for non-superadmins
    if not _is_super_admin(user) and tmpl.owner_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    if "title" in data:
        tmpl.title = (data["title"] or "Untitled Template").strip()[:512]
    if "description" in data:
        tmpl.template_description = (data["description"] or "").strip()[:512]
    if "icon" in data:
        tmpl.template_icon = (data["icon"] or "Document").strip()[:64]
    if "is_public" in data:
        tmpl.is_public = bool(data["is_public"])

    tmpl.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        "id": tmpl.id,
        "title": tmpl.title,
        "description": tmpl.template_description or "",
        "icon": tmpl.template_icon or "Document",
        "is_public": tmpl.is_public,
    })


@bp.delete("/admin/<int:tmpl_id>")
@jwt_required()
def admin_delete_template(tmpl_id: int):
    """Admin/Manager: soft-delete a template."""
    user = current_user()
    if not _can_manage_templates(user):
        return jsonify({"error": "Forbidden"}), 403

    tmpl = db.session.get(Document, tmpl_id)
    if not tmpl or not tmpl.is_template:
        return jsonify({"error": "Template not found"}), 404
        
    # Ownership check for non-superadmins
    if not _is_super_admin(user) and tmpl.owner_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    tmpl.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/admin/<int:tmpl_id>/publish")
@jwt_required()
def admin_publish_template(tmpl_id: int):
    """Admin/Manager: publish a template."""
    user = current_user()
    if not _can_manage_templates(user):
        return jsonify({"error": "Forbidden"}), 403

    tmpl = db.session.get(Document, tmpl_id)
    if not tmpl or not tmpl.is_template:
        return jsonify({"error": "Template not found"}), 404
        
    # Ownership check for non-superadmins
    if not _is_super_admin(user) and tmpl.owner_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    tmpl.is_public = True
    tmpl.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"id": tmpl.id, "is_public": True})


@bp.post("/admin/<int:tmpl_id>/unpublish")
@jwt_required()
def admin_unpublish_template(tmpl_id: int):
    """Admin/Manager: unpublish a template."""
    user = current_user()
    if not _can_manage_templates(user):
        return jsonify({"error": "Forbidden"}), 403

    tmpl = db.session.get(Document, tmpl_id)
    if not tmpl or not tmpl.is_template:
        return jsonify({"error": "Template not found"}), 404
        
    # Ownership check for non-superadmins
    if not _is_super_admin(user) and tmpl.owner_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    tmpl.is_public = False
    tmpl.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"id": tmpl.id, "is_public": False})
