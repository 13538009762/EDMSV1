"""AI Smart Assistant — Real integration with iFlytek Spark Lite (OpenAI Compatible)."""
from flask import Blueprint, request, Response, stream_with_context
import json
import requests

bp = Blueprint("ai", __name__)

# TODO: Replace with your actual APIPassword from iFlytek console
SPARK_API_PASSWORD = "XyuSepRzbdDVUKvIkpXV:boQXTGszIkfPLZYjOeiz"
SPARK_API_URL = "https://spark-api-open.xf-yun.com/v1/chat/completions"

SYSTEM_PROMPTS = {
    "summarize": "Summarize the following text concisely. Use Markdown formatting (bullet points, bold text) where appropriate. Output ONLY the summary.",
    "expand": "Expand on the following text with more detail and examples. Use Markdown (headings, lists, bold) for better structure. Output ONLY the expanded content.",
    "polish": "Polish the following text for clarity and professionalism. Keep the existing structure but use Markdown (bold, lists) if it improves readability. Output ONLY the polished version. Crucially, the output MUST be in the SAME LANGUAGE as the input text.",
    "translate_en": "Translate the following text into English. Preserve the original document structure using Markdown (headings, lists, bold). Output ONLY the translation.",
    "translate_zh": "请将以下文本翻译成简体中文。保持原有的文档结构（使用 Markdown 语法：标题、列表、加粗等）。只输出翻译结果，不要输出原文或解释。",
    "translate_ru": "Переведите следующий текст на русский язык. Сохраняйте структуру документа с помощью Markdown (заголовки, списки, жирный шрифт). Выводите ТОЛЬКО перевод.",
    "fix_punctuation": "Fix the punctuation in the following text. Correct mixed Chinese/English punctuation usage, normalize full-width/half-width marks, and fix spacing. Output ONLY the corrected text.",
    "chat": "You are a professional document specialist. Answer queries based ONLY on context. Use Markdown for structure. CRITICAL: 1. THE DOCUMENT CONTENT MUST BE PLAIN TEXT/MARKDOWN OUTSIDE ANY BLOCKS. 2. NEVER put the document text inside the JSON. 3. JSON is ONLY for metadata: ```json {\"action\": \"start_approval\", \"params\": {\"approvers\": [\"Name\"]}} ```. 4. If you output JSON, append it at the VERY END after your normal text response.",
    "auto_tag": "Analyze the text and provide 1-3 short category tags like [Finance], [HR]. Output ONLY the tags separated by commas, no explanations."
}

@bp.post("/generate")
def ai_generate():
    """Real AI generation endpoint using Spark Lite via SSE."""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    action = data.get("action", "")

    # For Lite models, merging instruction with user content is more reliable
    instruction = SYSTEM_PROMPTS.get(action, "You are a helpful assistant.")
    
    # 💡 Optimization: Use Chinese wrappers for Chinese-target tasks to reduce English bias
    if action in ['translate_zh', 'auto_tag'] or '请' in instruction:
        user_content = f"指令: {instruction}\n\n目标文本:\n{prompt}"
    else:
        user_content = f"Instruction: {instruction}\n\nTarget Text:\n{prompt}"
    
    # Spark Lite (OpenAI Compatible) construction
    payload = {
        "model": "lite",
        "messages": [
            {"role": "user", "content": user_content}
        ],
        "stream": True
    }
    
    headers = {
        "Authorization": f"Bearer {SPARK_API_PASSWORD}",
        "Content-Type": "application/json"
    }

    def generate():
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start'}, ensure_ascii=False)}\n\n"

            response = requests.post(SPARK_API_URL, headers=headers, json=payload, stream=True)
            
            if response.status_code != 200:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                yield f"data: {json.dumps({'type': 'chunk', 'content': error_msg}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                return

            for line in response.iter_lines():
                if not line:
                    continue
                    
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_str = line_text[6:].strip()
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        resp_json = json.loads(data_str)
                        content = resp_json['choices'][0]['delta'].get('content', '')
                        if content:
                            chunk = json.dumps({"type": "chunk", "content": content}, ensure_ascii=False)
                            yield f"data: {chunk}\n\n"
                    except (json.JSONDecodeError, KeyError):
                        continue

            # Send completion event
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'chunk', 'content': f'Connection error: {str(e)}'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
