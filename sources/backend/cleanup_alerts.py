from app import create_app
from app.extensions import db
from app.models.workflow import AuditLog
from sqlalchemy import func

app = create_app()
with app.app_context():
    # Find documents with multiple INTRUSION_ALERT logs
    duplicates = db.session.query(
        AuditLog.document_id, 
        func.count(AuditLog.id).label('count')
    ).filter_by(action='INTRUSION_ALERT').group_by(AuditLog.document_id).having(func.count(AuditLog.id) > 1).all()
    
    print(f"Found {len(duplicates)} documents with duplicate alerts.")
    
    for doc_id, count in duplicates:
        print(f"Doc ID {doc_id} has {count} alerts. Keeping only the first one.")
        # Get all alerts for this document, ordered by creation
        alerts = AuditLog.query.filter_by(document_id=doc_id, action='INTRUSION_ALERT').order_by(AuditLog.created_at.asc()).all()
        # Keep the first one, delete the rest
        for a in alerts[1:]:
            db.session.delete(a)
    
    db.session.commit()
    print("Cleanup complete.")
