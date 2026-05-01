from app import create_app
from app.extensions import db
from app.models.workflow import AuditLog

app = create_app()
with app.app_context():
    alerts = AuditLog.query.filter_by(action='INTRUSION_ALERT').all()
    print(f"Total alerts: {len(alerts)}")
    for a in alerts:
        print(f"ID: {a.id}, Summary: {repr(a.summary)}")
