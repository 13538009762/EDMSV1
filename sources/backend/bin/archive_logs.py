import os
import sys
import csv
from datetime import datetime, timedelta

# Ensure backend root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.core import AuditLog

def archive_audit_logs(days=30):
    """
    Stage 3: 合规日志冷热分离 (Log Archival)
    将超过指定天数的审计日志导出为 CSV 并从数据库中删除。
    """
    app = create_app()
    with app.app_context():
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 1. 查找冷数据
        logs = AuditLog.query.filter(AuditLog.created_at < cutoff_date).all()
        if not logs:
            print(f"[Archive] No logs older than {days} days found.")
            return

        # 2. 导出为 CSV
        archive_dir = os.path.join(os.getcwd(), "archives")
        os.makedirs(archive_dir, exist_ok=True)
        
        filename = f"audit_logs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(archive_dir, filename)
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "user_id", "action", "document_id", "ip_address", "summary", "created_at"])
            for log in logs:
                writer.writerow([
                    log.id, log.user_id, log.action, log.document_id, 
                    log.ip_address, log.summary, log.created_at
                ])
        
        # 3. 物理删除
        count = len(logs)
        AuditLog.query.filter(AuditLog.created_at < cutoff_date).delete()
        db.session.commit()
        
        print(f"[Success] Archived {count} log entries to {filepath}")
        print(f"[Cleanup] Deleted {count} cold entries from database.")

if __name__ == "__main__":
    # 默认清理 30 天以前的日志
    archive_audit_logs(30)
