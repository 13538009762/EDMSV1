from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required
from app.services.ai_service import AIService
from app.utils.auth import current_user
import json
import os
from datetime import datetime

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

def _add_wav_header(pcm_data):
    """Add a 44-byte WAV header to raw PCM data (16k, 16bit, mono)."""
    header = bytearray()
    header.extend(b'RIFF')
    header.extend((len(pcm_data) + 36).to_bytes(4, 'little'))
    header.extend(b'WAVEfmt ')
    header.extend((16).to_bytes(4, 'little'))
    header.extend((1).to_bytes(2, 'little'))
    header.extend((1).to_bytes(2, 'little'))
    header.extend((16000).to_bytes(4, 'little'))
    header.extend((32000).to_bytes(4, 'little'))
    header.extend((2).to_bytes(2, 'little'))
    header.extend((16).to_bytes(2, 'little'))
    header.extend(b'data')
    header.extend(len(pcm_data).to_bytes(4, 'little'))
    return header + pcm_data

@bp.post("/meeting-summary")
@jwt_required()
def meeting_summary():
    if "audio" not in request.files:
        return jsonify({"error": "No audio part"}), 400
    file = request.files["audio"]
    
    try:
        # Debug: Save audio file locally
        debug_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "debug_audio"))
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_filename = f"meeting_{timestamp}_{file.filename}"
        debug_path = os.path.join(debug_dir, debug_filename)
        
        # Save a copy (handle both PCM and WebM for now)
        pcm_data = file.read()
        if len(pcm_data) > 0:
            with open(debug_path, "wb") as f:
                # If it looks like PCM (no header), add one for playback
                if pcm_data[:4] != b'RIFF':
                    f.write(_add_wav_header(pcm_data))
                else:
                    f.write(pcm_data)
        
        file.seek(0)
        
        # Use real transcription
        text = AIService.transcribe_audio(file)
        
        # Generate a summary using AI after transcription
        summary_markdown = "### 语音转写结果\n" + text
        if len(text) > 20:
             # If text is long enough, try to generate a real summary
             # For now, just return the text as it's better than a mock
             pass

        return jsonify({
            "code": 200,
            "data": {
                "original_text": text,
                "summary_markdown": summary_markdown
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.post("/transcribe")
@jwt_required()
def ai_transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio part"}), 400
    file = request.files["audio"]
    
    try:
        # Debug: Save audio file locally to check if recording is working
        debug_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "debug_audio"))
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_filename = f"debug_{timestamp}_{file.filename}"
        debug_path = os.path.join(debug_dir, debug_filename)
        
        # Save a copy with WAV header
        pcm_data = file.read()
        wav_data = _add_wav_header(pcm_data)
        with open(debug_path, "wb") as f:
            f.write(wav_data)
        
        print(f"[DEBUG] Audio saved to: {debug_path}")
        
        # Reset file pointer for transcription service
        file.seek(0)

        text = AIService.transcribe_audio(file)
        return jsonify({
            "code": 200,
            "text": text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    
    # 1. 尝试使用向量搜索 (Semantic Search) + 增大 Top-K 确保历史数据覆盖
    contexts = search_documents(query, doc_ids=doc_ids, limit=20)
    
    # 2. 兜底策略：如果向量数据库没有返回结果，则直接从 MySQL 提取文档原文
    if not contexts:
        print(f"[AI QA] 向量搜索未返回结果 (Docs: {doc_ids})，正在尝试从数据库直接提取内容...")
        from app.models import Document
        from app.utils.text import extract_text_from_tiptap
        from app.extensions import db
        
        for did in doc_ids:
            doc = db.session.get(Document, did)
            if doc and doc.current_version:
                text = ""
                try:
                    # 尝试解析富文本内容
                    cj = json.loads(doc.current_version.content_json)
                    text = extract_text_from_tiptap(cj)
                except:
                    text = doc.title
                
                if text:
                    contexts.append({
                        "title": doc.title,
                        "text": text[:8000] # 增大兜底提取长度，确保历史深度
                    })
    
    context_text = "\n\n".join([f"文档片段 (来自《{c.get('title')}》):\n{c.get('text')}" for c in contexts])
    
    # We can stream the answer back using stream_chat
    messages = [
        {"role": "user", "content": f"""请严格根据提供的知识库文档回答，如果文档中没有提及，请回答‘文档中未提及’，不要自己编造。

【答题准则】：
1. 准确性：请仔细核对数值与指标的对应关系，不要将 A 指标的数值用于 B 指标。
2. 梳理过程与历史变迁：如果用户要求梳理某个特定实体（如某项业务、产品、人物或事件）的‘过程’、‘发展线’或‘历史变迁’，请你首先过滤出与该实体强相关的上下文。然后，必须严格按照时间先后顺序或事件发展的自然顺序进行提取和排列。绝不可颠倒时间线，也严禁在梳理过程中混入与该实体无关的其他干扰信息（如同一时期发生的其他无关事件）。当被要求列出历史数据时，必须使用项目符号按时间顺序逐一列出，例如：- 第一季度：[数据]；- 第二季度：[数据]。
3. 因果溯源：当你被问及‘为什么’或‘原因’时，必须严格在目标事件所属的特定时间节点或对应上下文段落中寻找答案。严禁跨越时间线或跨越不相关的实体（如用 A 事件/时间段的背景，去强行解释 B 事件/时间段的结果）。 如果检索到的文本中没有通过明确的因果连词（如‘因为’、‘由于’、‘导致’、‘受限于’、‘原因是’）写明原因，请直接回答‘提供的文档中未明确说明原因’，绝对严禁基于你的内部知识、商业常识或由于文本相邻而自行推导、缝合原因。
4. 时序隔离与状态过滤：请不要把不同时间发生的风险和事件混为一谈，仔细核对原文的发生时间。当询问‘最新’或‘目前’的挑战时，请检查该风险在最新的文档中是否已被标记为‘解除’或‘解决’，如果是，请将其排除。
5. 完整性：请一步一步思考（Let's think step by step），确保回答完整覆盖了用户提出的所有子问题。

待回答问题：
{query}

提供的知识库文档片段：
{context_text}"""}
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
    lang = data.get("lang", "zh")
    
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
        
    result = AIService.check_logic(text_content, ai_model=ai_model, lang=lang)
    return jsonify({"code": 200, "data": result})

def random_str(length):
    import random
    import string
    return "".join(random.choices(string.digits, k=length))
