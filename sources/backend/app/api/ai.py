"""AI Smart Assistant — Mock SSE endpoint for frontend integration testing."""
from flask import Blueprint, request, Response, stream_with_context
import time
import json

bp = Blueprint("ai", __name__)

# Mock response templates for different AI actions
MOCK_RESPONSES = {
    "summarize": "Based on the selected text, here is a concise summary: The document outlines key points regarding {topic}. The main takeaways are: 1) Strategic alignment with company goals, 2) Clear timeline and milestones, 3) Resource allocation and budget considerations. This summary captures the essence of the original content while maintaining brevity.",
    "expand": "Let me elaborate on this point in greater detail.\n\nThe concept discussed here has several important dimensions worth exploring. First, from a strategic perspective, this approach aligns with industry best practices and has been validated by numerous case studies. Second, the implementation details require careful consideration of technical constraints, team capacity, and timeline dependencies. Third, the expected outcomes include improved efficiency, reduced costs, and enhanced stakeholder satisfaction.\n\nFurthermore, it is worth noting that similar initiatives in comparable organizations have yielded positive results, with an average improvement rate of 25-30% in key performance indicators.",
    "polish": "Here is the polished version of the text with improved clarity, tone, and professionalism:\n\nThe aforementioned initiative represents a significant step forward in our organizational development strategy. By leveraging cutting-edge methodologies and drawing upon established best practices, we aim to deliver measurable improvements across all key performance areas. Our commitment to excellence is reflected in the meticulous planning and rigorous execution framework outlined herein.",
    "translate_en": "Here is the English translation:\n\nThis document presents a comprehensive overview of the project scope, objectives, and deliverables. The implementation plan follows a phased approach to ensure quality and minimize risk. Key stakeholders have been identified and their roles clearly defined throughout the project lifecycle.",
    "translate_zh": "以下是中文翻译：\n\n本文件全面概述了项目范围、目标和可交付成果。实施计划采用分阶段推进方式，以确保质量并降低风险。关键利益相关者已被明确识别，其在整个项目生命周期中的角色也已清晰定义。",
    "translate_ru": "Вот перевод на русский язык:\n\nДанный документ представляет собой комплексный обзор области проекта, целей и результатов. План реализации следует поэтапному подходу для обеспечения качества и минимизации рисков. Ключевые заинтересованные стороны определены, и их роли чётко распределены на протяжении всего жизненного цикла проекта.",
}

DEFAULT_RESPONSE = "This is a simulated AI response. In production, this generator will be replaced by a real LLM API call (e.g., DeepSeek, OpenAI GPT). The frontend SSE streaming integration is working correctly — each character is delivered in real-time to create the typewriter effect you see now."


@bp.post("/generate")
def mock_ai_generate():
    """Mock AI generation endpoint using Server-Sent Events (SSE)."""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    action = data.get("action", "")

    # Pick the appropriate mock response
    topic = prompt[:50] if prompt else "the subject matter"
    mock_text = MOCK_RESPONSES.get(action, DEFAULT_RESPONSE)
    mock_text = mock_text.format(topic=topic) if "{topic}" in mock_text else mock_text

    def generate():
        # Send initial event
        yield f"data: {json.dumps({'type': 'start'})}\n\n"

        # Stream character by character
        for char in mock_text:
            chunk = json.dumps({"type": "chunk", "content": char})
            yield f"data: {chunk}\n\n"
            time.sleep(0.02)  # 20ms per character — fast but visible typewriter

        # Send completion event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
