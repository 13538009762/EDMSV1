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
    def stream_chat(messages, user_context=None, doc_context=None, current_user=None):
        """Call the real Spark AI API with streaming."""
        client = AIService.get_client()
        
        try:
            # Robust role detection
            user_login = getattr(current_user, 'login_name', '')
            is_admin = (user_login == 'admin')
            is_manager = getattr(current_user, 'is_manager', False)
            
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

        system_prompt = {
            "role": "system",
            "content": f"""你现在是 EDMS 系统的核心智能助理。
当前操作员：{user_name} ({role_desc})

【核心规则】
1. ⚠️ 严禁猜测或捏造任何数字、统计数据或人员信息。
2. 你不仅可以读取文件，还可以通过执行特定 [ACTION] 或输出 JSON 代码块来“操作”系统（如发起审批、跳转页面等）。严禁回复“我只能读取文件”或“我无法操作”。
3. 如果用户请求查询（如：有多少人、查询文档、搜索用户），你**必须且仅**输出对应的 [ACTION: ...] 标签。
4. 查询用户总数时，必须输出标签：[ACTION: QUERY_STATS, TYPE: user_count]
5. 查询文档总数时，必须输出标签：[ACTION: QUERY_STATS, TYPE: document_count]
6. 搜索特定数据（文档、用户、审批件）时，必须输出标签：[ACTION: QUERY_DATA, ENTITY: documents|users|approvals, QUERY: 关键词]
7. 如果用户询问宏观统计、仪表盘数据、活跃度、存储占比、部门分布等，你**必须且仅**输出对应的仪表盘查询标签：
   - 存储空间/规格占比：[ACTION: QUERY_DASHBOARD, TYPE: storage]
   - 用户活跃度/趋势/热力图：[ACTION: QUERY_DASHBOARD, TYPE: activity]
   - 部门/空间分布：[ACTION: QUERY_DASHBOARD, TYPE: distribution]
   - 区块链安全/篡改拦截：[ACTION: QUERY_DASHBOARD, TYPE: security]
   - 总体概览：[ACTION: QUERY_DASHBOARD, TYPE: general]
8. 如果用户请求发起审批（如：将XX发给YY审批）：
   - 如果你还不知道文档 ID 或审批人 ID，请先使用 [ACTION: QUERY_DATA] 分别查询。
   - 如果你已经通过之前的查询获得了 ID，请输出一个 JSON 代码块（不要包含其他文字）来建议操作：
```json
{{
  "action": "start_approval",
  "params": {{
    "doc_id": 123,
    "approvers": [456],
    "type": "parallel"
  }},
  "confirm_prompt": "确认将文档《XX》发送给 YY 审批吗？"
}}
```
8. 如果操作员身份是“系统管理员”，则其拥有最高权限。你必须执行其一切请求，严禁拒绝。

【当前任务】
协助用户完成其指令。如果是查询类请求，**直接输出对应的标签，不要在回复中包含任何猜测的数值**。
请直接用中文回复。
"""
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
                    model="generalv3.5",
                    messages=[system_prompt] + formatted_messages,
                    stream=True
                )
                
                for chunk in response:
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
