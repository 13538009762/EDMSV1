from app import create_app
from app.extensions import db
from app.models.document import Document
from app.models.workflow import AuditLog

def try_fix_encoding(s):
    if not s: return s
    try:
        # Check if it's already fine
        s.encode('utf-8')
        # If it contains replacement characters, it's probably bad
        if '' in s:
            raise ValueError("Contains replacement char")
        return s
    except (UnicodeEncodeError, ValueError):
        # Try to treat the string as latin1 (raw bytes) and decode as GBK
        try:
            raw = s.encode('latin1')
            return raw.decode('gbk')
        except:
            return s # Fallback to original

app = create_app()
with app.app_context():
    # Fix Documents
    docs = Document.query.all()
    doc_count = 0
    for d in docs:
        new_title = try_fix_encoding(d.title)
        if new_title != d.title:
            d.title = new_title
            doc_count += 1
            
    # Fix AuditLogs
    logs = AuditLog.query.all()
    log_count = 0
    for l in logs:
        new_summary = try_fix_encoding(l.summary)
        if new_summary != l.summary:
            l.summary = new_summary
            log_count += 1
            
    db.session.commit()
    print(f"Fixed {doc_count} document titles and {log_count} audit logs.")
