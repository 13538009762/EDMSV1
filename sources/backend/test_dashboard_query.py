from app import create_app
from app.extensions import db
from app.models.workflow import AuditLog
from sqlalchemy import func

app = create_app()
with app.app_context():
    try:
        # Test the specific query that I added
        tamper_alerts = db.session.query(func.count(func.distinct(AuditLog.document_id))).filter(AuditLog.action == 'INTRUSION_ALERT').scalar() or 0
        print(f"Tamper alerts count: {tamper_alerts}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
