from app import create_app
from app.extensions import db
from app.models.core import User, Department
from app.models.document import Document, DocumentPermission, DocumentVersion
from app.models.space import Space
from app.models.workflow import ApprovalFlow, ApprovalParticipant, AuditLog
from sqlalchemy import func, text, or_
from datetime import datetime, timedelta
import os
import json

app = create_app()
with app.app_context():
    user = User.query.filter_by(login_name='admin').first()
    is_admin = True
    
    def get_authorized_filter():
        if is_admin:
            return (Document.is_template == False, Document.deleted_at == None)
        return (Document.is_template == False, Document.deleted_at == None) # Simplified

    auth_filter = get_authorized_filter()

    # Let's run the blockchain part which I modified
    try:
        on_chain_count = Document.query.filter(Document.tx_hash != None).count()
        tamper_alerts = db.session.query(func.count(func.distinct(AuditLog.document_id))).filter(AuditLog.action == 'INTRUSION_ALERT').scalar() or 0
        print(f"On chain: {on_chain_count}, Tamper alerts: {tamper_alerts}")
        
        # Check if tamper_logs query works
        tamper_logs = AuditLog.query.filter_by(action='INTRUSION_ALERT')\
            .order_by(AuditLog.created_at.desc()).limit(5).all()
        print(f"Found {len(tamper_logs)} tamper logs")
        for log in tamper_logs:
            print(f"  - {log.id}: {log.summary} (User: {log.user.display_name() if log.user else 'None'})")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
