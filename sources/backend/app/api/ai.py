from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required
from app.services.ai_service import AIService
from app.utils.auth import current_user
import json

bp = Blueprint("ai", __name__)

@bp.post("/chat")
@jwt_required()
def ai_chat():
    try:
        data = request.get_json(silent=True) or {}
        messages = data.get("messages", [])
        context_url = data.get("context_url", "")
        doc_context = data.get("doc_context", "")

        ai_model = data.get("ai_model", "spark-lite")
        user = current_user()
        user_info = {
            "id": user.id if user else 0,
            "login_name": user.login_name if user else "guest"
        }
        
        from app.extensions import db
        db.session.remove()
        
        return Response(
            stream_with_context(AIService.stream_chat(
                messages, 
                user_context=context_url, 
                doc_context=doc_context, 
                current_user=user_info,
                ai_model=ai_model
            )),
            mimetype="text/event-stream"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
@bp.route("/generate", methods=["POST"])
@jwt_required()
def ai_generate():
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    action = data.get("action", "")
    lang = data.get("lang", "zh")
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
        
    ai_model = data.get("ai_model", "spark-lite")
    
    from app.extensions import db
    db.session.remove()
    
    return Response(
        stream_with_context(AIService.stream_generate(prompt, action, lang, ai_model=ai_model)),
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
        doc.current_version = ver # 💡 Use object relationship to ensure ID is handled correctly
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

@bp.get("/history")
@jwt_required()
def get_ai_history():
    from app.services.ai_history_store import ai_history_store
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    doc_id = request.args.get("document_id", type=int)
    
    # Only admin can see all, users see their own
    user = current_user()
    user_id = None if user.login_name == 'admin' else user.id
    
    history = ai_history_store.get_all(page=page, per_page=per_page, document_id=doc_id, user_id=user_id)
    return jsonify({
        "code": 200,
        "data": history
    })

@bp.delete("/history/<int:history_id>")
@jwt_required()
def delete_ai_history(history_id):
    from app.services.ai_history_store import ai_history_store
    success = ai_history_store.delete(history_id)
    if success:
        return jsonify({"code": 200, "message": "Success"})
    return jsonify({"error": "Not found"}), 404

@bp.post("/cross-qa")
@jwt_required()
def cross_document_qa():
    data = request.get_json(silent=True) or {}
    doc_ids = data.get("doc_ids", [])
    query = data.get("query", "")
    ai_model = data.get("ai_model", "spark-lite")
    
    if not doc_ids or not query:
        return jsonify({"error": "Missing doc_ids or query"}), 400
        
    from app.services.vector_store import search_documents
    
    # Search top 5 chunks across the selected documents
    contexts = search_documents(query, doc_ids=doc_ids, limit=5)
    
    context_text = "\n\n".join([f"文档片段 (来自《{c.get('title')}》):\n{c.get('text')}" for c in contexts])
    
    # We can stream the answer back using stream_chat
    messages = [
        {"role": "user", "content": f"请结合以下文档片段回答问题：\n{query}\n\n{context_text}"}
    ]
    user = current_user()
    user_info = {
        "id": user.id if user else 0,
        "login_name": user.login_name if user else "guest"
    }
    
    from app.extensions import db
    db.session.remove()
    
    return Response(
        stream_with_context(AIService.stream_chat(
            messages, 
            user_context="多文档联合分析", 
            doc_context="", 
            current_user=user_info,
            ai_model=ai_model
        )),
        mimetype="text/event-stream"
    )

@bp.post("/check-logic")
@jwt_required()
def check_logic():
    data = request.get_json(silent=True) or {}
    doc_id = data.get("doc_id")
    ai_model = data.get("ai_model", "spark-lite")
    
    if not doc_id:
        return jsonify({"error": "Missing doc_id"}), 400
        
    from app.models import Document
    from app.extensions import db
    doc = db.session.get(Document, doc_id)
    if not doc or not doc.current_version:
        return jsonify({"error": "Document not found"}), 404
        
    ver = doc.current_version
    text_content = ""
    try:
        cj = json.loads(ver.content_json) if isinstance(ver.content_json, str) else ver.content_json
        from app.api.documents import _extract_text_from_tiptap
        text_content = _extract_text_from_tiptap(cj)
    except Exception:
        text_content = doc.title
        
    # IMPORTANT: Release connection back to pool before slow network IO!
    db.session.remove()
        
    result = AIService.check_logic(text_content, ai_model=ai_model)
    return jsonify({"code": 200, "data": result})

def random_str(length):
    import random
    import string
    return "".join(random.choices(string.digits, k=length))
