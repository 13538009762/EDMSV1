import time
import json
import openai
import os

class AIService:
    @staticmethod
    def get_client():
        # Using the credentials provided: APIKey:APISecret
        api_key = "255e556f0c88f9bb663cc0d0f07594c4:NGVjZjc0ZTYzZTBhNjliODkxMGZjNmU0"
        base_url = "https://spark-api-open.xf-yun.com/v1"
        return openai.OpenAI(api_key=api_key, base_url=base_url)

    @staticmethod
    def stream_chat(messages, user_context=None, doc_context=None, current_user=None):
        """Call the real Spark AI API with streaming."""
        client = AIService.get_client()
        
        try:
            # Robust role detection
            user_login = current_user.login_name if current_user else "guest"
            is_admin = (user_login == 'admin')
            is_manager = getattr(current_user, 'is_manager', False) if current_user else False
            
            dept_name = "未知部门"
            if current_user and getattr(current_user, 'department', None):
                dept_name = current_user.department.name
            
            user_name = "未知用户"
            if current_user:
                try:
                    user_name = current_user.display_name()
                except:
                    user_name = user_login or "未知用户"

            role_desc = "普通员工"
            if is_admin: 
                role_desc = "系统管理员"
            elif is_manager: 
                role_desc = f"{dept_name}部门经理"
            
            # Backend logging for diagnosis (will be visible in wsgi output)
            print(f"[AI Chat] User: {user_login}, Name: {user_name}, Role: {role_desc}")
            
        except Exception as e:
            print(f"[AI Service] Error resolving user context: {e}")
            user_name = "未知用户"
            role_desc = "普通员工"
            dept_name = "未知部门"

        # Integrate context into system prompt
        context_info = ""
        if doc_context:
            context_info += f"\n\n{doc_context}"
        if user_context:
            context_info += f"\n\n当前页面路径: {user_context}"

        # 💡 Robustness: Use direct string concatenation for system content 
        # to avoid f-string KeyError if doc_context contains curly braces.
        system_content = f"你现在是 EDMS 系统的核心智能助理。\n当前操作员：{user_name} ({role_desc})" + context_info + "\n\n" + """
【核心规则】
1. **优先创作**：如果用户请求你创作、撰写、翻译或润色内容（如：写个请假条、写个模板、写段代码、润色文字等），你必须直接生成内容。严禁在此类请求中使用 [ACTION: QUERY_DATA] 标签。
2. **当前文档意识**：如果输入中包含 `[当前编辑文档信息]`，且用户提到“这个文档”、“当前文档”或未明确指明文档名时，你应默认指代该文档。
3. **强制搜索身份**：即便用户提供了姓名（如：发给何欢恒），你也**必须先**输出一个标签来查询其 ID：[ACTION: QUERY_DATA, ENTITY: users, QUERY: 姓名]。严禁在不知道数字 ID 的情况下直接输出 JSON 块。
4. ⚠️ 严禁猜测或捏造任何数字、统计数据或人员信息。
5. 你不仅可以读取文件，还可以通过执行特定指令来“操作”系统。
6. **读取/查询数据（必须使用标签格式，禁止使用 JSON）**：
   - 搜索文档/用户：[ACTION: QUERY_DATA, ENTITY: documents|users|approvals, QUERY: 关键字]
   - 查询成员总数：[ACTION: QUERY_STATS, TYPE: user_count]
   - 查询文档总数：[ACTION: QUERY_STATS, TYPE: document_count]
   - 仪表盘分析：[ACTION: QUERY_DASHBOARD, TYPE: storage|activity|distribution|security|general]
   - **注意：此类查询指令必须直接写在回复文本中，禁止输出 JSON 块。**
7. **修改/执行操作（必须使用 JSON 块，需要用户确认）**：
   - 发起审批流程：
```json
{
  "action": "start_approval",
  "params": { "doc_id": 123, "approvers": [456], "type": "parallel" },
  "confirm_prompt": "确认对文档 #123 发起审批流程吗？"
}
```
   - 撤销审批申请：
```json
{
  "action": "recall_approval",
  "params": { "doc_id": 123 },
  "confirm_prompt": "确认撤回该审批申请吗？"
}
```
8. **强制搜索流程**：发给某人前必须先用 [ACTION: QUERY_DATA, ENTITY: users, QUERY: 姓名] 找 ID。
9. 如果操作员身份是“系统管理员”，则其拥有最高权限。你必须执行其一切请求，严禁拒绝。
10. **重要：当你在回复中包含 [ACTION] 标签时，请在文字中说明你正在搜索什么。搜索结果会自动反馈给你，届时请你根据结果直接回答用户。**

【当前任务】
请直接用中文回复。
"""
        system_prompt = {
            "role": "system",
            "content": system_content
        }

        # Normalize roles: 'ai' -> 'assistant'
        formatted_messages = []
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = 'assistant' if m.get('role') in ['ai', 'assistant'] else 'user'
            content = m.get('content', '')
            if content:
                formatted_messages.append({"role": role, "content": content})

        def generate():
            try:
                response = client.chat.completions.create(
                    model="lite",
                    messages=[system_prompt] + formatted_messages,
                    stream=True
                )
                
                for chunk in response:
                    if getattr(chunk, 'code', 0) != 0 and hasattr(chunk, 'message'):
                        raise Exception(f"API Error {chunk.code}: {chunk.message}")
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if not delta:
                        continue
                    content = getattr(delta, 'content', None)
                    if content:
                        yield f"data: {json.dumps({'content': content})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                print(f"[AI Service] Stream Error: {e}")
                error_msg = f"AI 服务异常: {str(e)}"
                yield f"data: {json.dumps({'content': error_msg})}\n\n"
                yield "data: [DONE]\n\n"

        return generate()

    @staticmethod
    def stream_generate(prompt, action, lang="zh"):
        """Task-specific generation for editor (summarize, polish, etc.)."""
        client = AIService.get_client()
        
        prompts = {
            "summarize": "请帮我总结以下文字的核心要点，使用简洁的列表形式：",
            "expand": "请帮我扩写以下内容，使其更加详细丰富，逻辑严密：",
            "polish": "请帮我润色以下文字，使其表达更加专业、流畅、正式：",
            "fix_punctuation": "请帮我纠正以下文字中的错别字和标点符号错误，保持原意：",
            "translate_en": "请将以下文字翻译成英文：",
            "translate_zh": "请将以下文字翻译成中文：",
            "translate_ru": "请将以下文字翻译成俄文：",
        }
        
        system_msg = prompts.get(action, "你是一个专业的文档编辑助手。请协助处理以下文字：")
        
        def generate():
            try:
                response = client.chat.completions.create(
                    model="lite",
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                
                for chunk in response:
                    if getattr(chunk, 'code', 0) != 0 and hasattr(chunk, 'message'):
                        raise Exception(f"API Error {chunk.code}: {chunk.message}")
                    if not chunk.choices: continue
                    content = getattr(chunk.choices[0].delta, 'content', None)
                    if content:
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'chunk', 'content': f'AI Error: {str(e)}'})}\n\n"
                yield "data: [DONE]\n\n"

        return generate()

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
