from app import create_app
from app.extensions import db
from app.models import Document, User, Department
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("--- Database Diagnostics ---")
    try:
        # Total users
        user_count = db.session.query(User).count()
        print(f"Total Users in DB: {user_count}")
        
        # Total documents without filters
        total_raw = db.session.query(Document).count()
        print(f"Total Raw Documents: {total_raw}")
        
        # Documents with filters
        total_filtered = db.session.query(Document).filter(
            Document.is_template == False,
            Document.deleted_at == None
        ).count()
        print(f"Filtered Documents (Not Template, Not Deleted): {total_filtered}")
        
        # Check specific statuses
        from sqlalchemy import func
        status_counts = db.session.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
        print(f"Status breakdown (All): {status_counts}")
        
        # Check first 5 docs titles
        docs = Document.query.limit(5).all()
        for d in docs:
            print(f"Found Doc: ID={d.id}, Title='{d.title}', IsTemplate={d.is_template}, DeletedAt={d.deleted_at}")
            
    except Exception as e:
        print(f"DIAGNOSTIC CRASHED: {e}")
