import time
import json
import openai
import os

class AIService:
    @staticmethod
    def get_client():
        # Using the credentials provided: APIKey:APISecret
        api_key = "XyuSepRzbdDVUKvIkpXV:boQXTGszIkfPLZYjOeiz"
        base_url = "https://spark-api-open.xf-yun.com/v1"
        return openai.OpenAI(api_key=api_key, base_url=base_url)

    @staticmethod
    def stream_chat(messages, user_context=None, doc_context=None):
        """Call the real Spark AI API with streaming."""
        client = AIService.get_client()
        
        system_prompt = {
            "role": "system",
            "content": f"""你现在是 EDMS (Enterprise Document Management System) 的全能 AI 助手。
你的目标是协助用户高效管理文档、处理工作流。

系统当前上下文: {user_context or '主界面'}
{f'当前文档内容片段: {doc_context}' if doc_context else ''}

能力与暗号指南 (必须严格遵守):
1. **打开文档**: 当用户想查看或打开某个具体编号/ID的文档时，在回复结尾附加标签：[ACTION: OPEN_DOC, ID: 文档编号]
2. **查询统计**: 当用户询问文档总数、拦截次数等数据时，必须输出标签：[ACTION: QUERY_STATS, TYPE: document_count] (或其他相关类型)
3. **发起审批**: 依然使用 JSON 格式建议：
   ```json
   {{
     "action": "start_approval",
     "params": {{ "approvers": ["admin"], "type": "parallel" }}
   }}
   ```

注意：
- 查询类操作 (OPEN_DOC, QUERY_STATS) 是自动执行的，无需确认。
- 只有敏感操作 (如 start_approval) 才需要输出 JSON 块进行二次确认。
- 保持专业、简洁、礼貌。
"""
        }

        # Normalize roles: 'ai' -> 'assistant'
        formatted_messages = []
        for m in messages:
            role = 'assistant' if m['role'] in ['ai', 'assistant'] else 'user'
            formatted_messages.append({"role": role, "content": m['content']})

        try:
            response = client.chat.completions.create(
                model="generalv3.5", # Spark 3.5
                messages=[system_prompt] + formatted_messages,
                stream=True
            )
            
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = f"AI 服务异常: {str(e)}"
            yield f"data: {json.dumps({'content': error_msg})}\n\n"
            yield "data: [DONE]\n\n"

    @staticmethod
    def ocr_and_format(image_file):
        """For now, we keep OCR as a high-quality mock or use Spark's Multimodal if available."""
        # Spark's chat completions API might not support direct image upload like this.
        # Keeping simulated for stability unless specific OCR API is provided.
        time.sleep(2)
        markdown_content = """# 图片识别生成的结构化文档\n\n## 核心内容摘要\n识别到一份业务合作协议草案。关键点：双方责任明确，包含违约责任条款。建议发起法务合规审批。"""
        return {
            "title": f"图片识别建档_{time.strftime('%Y%m%d_%H%M')}",
            "content": markdown_content
        }

    @staticmethod
    def process_meeting_audio(audio_file):
        time.sleep(3)
        original_text = "讨论了项目 A 的进度。小李负责后端，下周五交付。小张负责前端，下周三交付。"
        summary_markdown = """### 会议纪要\n- **后端**: 下周五交付 (负责人: 小李)\n- **前端**: 下周三交付 (负责人: 小张)"""
        return {
            "original_text": original_text,
            "summary_markdown": summary_markdown
        }
