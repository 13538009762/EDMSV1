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
    "chat": "You are a professional document specialist. Answer queries based ONLY on context. Use Markdown for structure. \n\nCRITICAL LOGIC (核心逻辑):\n0. LANGUAGE RULE (语言规则): The entire output (outside JSON) MUST be in the SAME LANGUAGE as the User's Question.\n1. DRAFT FIRST: If the user asks to 'draft', 'write', or 'summarize', PROVIDE THE CONTENT. (如果用户要求起草或编写文档，请直接输出正文内容。)\n2. NO NAME, NO ACTION: Only suggest 'start_approval' IF the user specifically mentions a REAL NAME from the context. (只有在用户提到了上下文中的真实姓名时，才建议发起审批。)\n3. NO PLACEHOLDERS: NEVER suggest names like 'Zhang San' (张三) or 'Placeholder'. If no real name is found, DO NOT output any JSON. (严禁杜撰姓名如“张三”。如果没有真实姓名，严禁输出 JSON。)\n\nACTION FORMAT (only if name exists):\n```json {\"action\": \"start_approval\", \"params\": {\"approvers\": [\"<ACTUAL_NAME>\"], \"type\": \"parallel\"}} ```.\nAppend it at the VERY END. NEVER put draft text inside JSON.",
    "auto_tag": "Analyze the text and provide 1-3 short category tags like [Finance], [HR]. Output ONLY the tags separated by commas, no explanations."
}

@bp.post("/generate")
def ai_generate():
    """Real AI generation endpoint using Spark Lite via SSE."""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    action = data.get("action", "")

    instruction = SYSTEM_PROMPTS.get(action, "You are a helpful assistant.")

    # Standard OpenAI-compatible message structure for better instruction following
    payload = {
        "model": "lite",
        "messages": [
            {"role": "system", "content": instruction},
            {"role": "user", "content": prompt}
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
