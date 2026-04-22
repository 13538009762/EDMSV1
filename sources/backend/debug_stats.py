import os
import sys
from datetime import datetime, timedelta, date

# Add the project directory to path
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.models.core import User, Department
from app.models.document import Document, DocumentVersion, DocumentPermission
from app.models.workflow import ApprovalFlow, AuditLog
from sqlalchemy import func, text, or_

app = create_app()

def debug_stats():
    with app.app_context():
        # 1. Simulating admin user
        user = User.query.filter_by(login_name='admin').first()
        if not user:
            print("ERROR: User 'admin' not found!")
            return
        
        print(f"Executing stats as user: {user.login_name} (ID: {user.id})")
        
        is_admin = user.login_name == 'admin'
        
        def get_authorized_filter():
            if is_admin:
                return (Document.is_template == False, Document.deleted_at == None)
            return () # truncated for debug

        auth_filter = get_authorized_filter()
        print(f"Auth Filter: {auth_filter}")

        # Basic counts
        total_users = User.query.filter_by(registration_status='active').count()
        total_docs = Document.query.filter(*auth_filter).count()
        print(f"Total Users: {total_users}")
        print(f"Total Docs: {total_docs}")

        # Status distribution
        raw_status = db.session.query(Document.status, func.count(Document.id))\
            .filter(*auth_filter)\
            .group_by(Document.status).all()
        print(f"Status Data: {raw_status}")

        # Trend data check
        today_dt = datetime.now()
        thirty_days_ago = today_dt - timedelta(days=30)
        
        docs_subq = db.session.query(Document.id).filter(*auth_filter).subquery()
        
        try:
            doc_q = db.session.query(func.date(Document.updated_at), func.count(Document.id))\
                .filter(Document.id.in_(docs_subq))\
                .filter(Document.updated_at >= thirty_days_ago)\
                .group_by(func.date(Document.updated_at)).all()
            print(f"Trend Doc Query Results: {doc_q}")
        except Exception as e:
            print(f"Trend Query FAILED: {e}")

if __name__ == "__main__":
    debug_stats()
