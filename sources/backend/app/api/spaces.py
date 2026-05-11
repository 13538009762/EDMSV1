from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.space import Space
from app.models.document import Document, DocumentVersion
from app.utils.auth import current_user
import json
from datetime import datetime

bp = Blueprint("spaces", __name__)

@bp.get("")
@jwt_required()
def list_spaces():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    spaces = Space.query.all()
    items = []
    for s in spaces:
        items.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "owner_login": s.owner.login_name if s.owner else None,
            "created_at": s.created_at.isoformat() + "Z" if s.created_at else None
        })
    return jsonify({"items": items})

@bp.post("")
@jwt_required()
def create_space():
    user = current_user()
    if not user or not user.is_manager:
        return jsonify({"error": "Forbidden: Only managers can create spaces"}), 403
    
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "New Space").strip()[:256]
    name_en = (data.get("name_en") or "").strip()[:256]
    description = (data.get("description") or "").strip()
    
    s = Space(name=name, name_en=name_en, description=description, owner_id=user.id)
    db.session.add(s)
    db.session.commit()
    
    return jsonify({
        "id": s.id,
        "name": s.name,
        "description": s.description,
    }), 201

@bp.get("/templates")
@jwt_required()
def list_templates():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    templates = Document.query.filter_by(is_template=True, is_public=True).all()
    items = []
    for t in templates:
        items.append({
            "id": t.id,
            "title": t.title,
            "description": "Standard Document Template", # We don't have a desc field on Document, returning default
            "created_at": t.created_at.isoformat() + "Z" if t.created_at else None,
            "owner_name": t.owner.display_name() if t.owner else "System"
        })
    return jsonify({"items": items})

@bp.post("/templates/<int:tmpl_id>/create-from")
@jwt_required()
def clone_from_template(tmpl_id: int):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    tmpl = db.session.get(Document, tmpl_id)
    if not tmpl or not tmpl.is_template:
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
        except:
            doc_number = f"{today_str}001"
    else:
        doc_number = f"{today_str}001"
        
    doc = Document(owner_id=user.id, title=f"New from {tmpl.title}", status="draft", doc_number=doc_number)
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
    
    return jsonify({
        "id": doc.id,
        "title": doc.title
    }), 201
