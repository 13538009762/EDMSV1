import re

with open('app/api/documents.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the else block using regex to be perfectly insensitive to trailing whitespaces and line endings
target_pattern = r'    else:\s+# 只要 Navicat 里被人改了一个字，这里绝对不相等！'

replacement = '''    else:
        # ======= 新增：真正把内鬼行为写入数据库 =======
        from app.models.workflow import AuditLog
        from flask import request
        user = current_user()
        
        tamper_log = AuditLog(
            user_id=user.id if user else None,
            document_id=doc.id,             
            action='ALERT_TAMPER',          
            ip_address=request.remote_addr, 
            summary='【零信任预警】底层哈希校验失败，检测到严重的数据篡改行为！' 
        )
        db.session.add(tamper_log)
        db.session.commit()
        # ==============================================='''

new_text = re.sub(target_pattern, replacement, text)

with open('app/api/documents.py', 'w', encoding='utf-8') as f:
    f.write(new_text)
