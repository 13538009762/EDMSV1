from app import create_app
from app.extensions import db
from app.models.document import Document
from app.models.workflow import AuditLog
from app.models.core import Department, User

def fix(s):
    if not s: return s
    try:
        # If it contains the replacement character, it's definitely mangled
        if '\ufffd' in s:
            # Try the latin1 -> gbk trick
            try:
                return s.encode('latin1').decode('gbk')
            except:
                # If that fails, just strip the junk or use a placeholder
                return s.replace('\ufffd', '?')
        return s
    except:
        return s

app = create_app()
with app.app_context():
    # Fix Documents
    docs = Document.query.all()
    for d in docs:
        if d.title and '\ufffd' in d.title:
            try:
                d.title = d.title.encode('latin1').decode('gbk')
            except:
                pass
            
    # Fix AuditLogs
    logs = AuditLog.query.all()
    for l in logs:
        if l.summary and '\ufffd' in l.summary:
            try:
                l.summary = l.summary.encode('latin1').decode('gbk')
            except:
                pass
                
    db.session.commit()
    print("Done")
