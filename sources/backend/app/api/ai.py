from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required
from app.services.ai_service import AIService
from app.utils.auth import current_user
import json

bp = Blueprint("ai", __name__)

@bp.post("/chat")
@jwt_required()
def ai_chat():
    data = request.get_json() or {}
    messages = data.get("messages", [])
    context_url = data.get("context_url", "")
    
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
        
    return Response(
        stream_with_context(AIService.stream_chat(messages, context_url, current_user=current_user())),
        mimetype="text/event-stream"
    )
@bp.route("/generate", methods=["POST"])
@jwt_required()
def ai_generate():
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    action = data.get("action", "")
    lang = data.get("lang", "zh")
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
        
    return Response(
        stream_with_context(AIService.stream_generate(prompt, action, lang)),
        mimetype="text/event-stream"
    )

@bp.post("/import-image")
@jwt_required()
def import_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    
    result = AIService.ocr_and_format(file)
    
    # Create document in DB (Simplified for now)
    from app.models import Document, DocumentVersion
    from app.extensions import db
    user = current_user()
    
    try:
        from datetime import datetime
        today_str = datetime.now().strftime("%Y%m%d")
        # Logic to generate doc number if needed, but let's keep it simple
        doc_number = f"IMG{today_str}{random_str(3)}" 
        
        doc = Document(
            owner_id=user.id,
            title=result["title"],
            status="draft",
            doc_number=doc_number
        )
        db.session.add(doc)
        db.session.flush()
        
        ver = DocumentVersion(
            document_id=doc.id,
            version_no=1,
            content_json=json.dumps({"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": result["content"]}]}]}), # Simplified
            created_by_id=user.id
        )
        # Actually it's better to store as Markdown if the system supports it, 
        # but the current system seems to use Tiptap JSON. 
        # For simplicity, we'll return the ID and content preview.
        
        db.session.add(ver)
        doc.current_version_id = ver.id
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "data": {
                "document_id": doc.id,
                "title": doc.title,
                "content_preview": result["content"][:200]
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.post("/meeting-summary")
@jwt_required()
def meeting_summary():
    if "audio" not in request.files:
        return jsonify({"error": "No audio part"}), 400
    file = request.files["audio"]
    
    result = AIService.process_meeting_audio(file)
    return jsonify({
        "code": 200,
        "data": result
    })

def random_str(length):
    import random
    import string
    return "".join(random.choices(string.digits, k=length))
