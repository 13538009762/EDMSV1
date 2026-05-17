import os
import sys
from datetime import datetime

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wsgi import app
from app.extensions import db
from app.models import Document, User

def wash():
    with app.app_context():
        # 1. Update is_super_admin for admin user
        admin = User.query.filter_by(login_name='admin').first()
        if admin:
            print(f"Setting is_super_admin = True for user: {admin.login_name}")
            admin.is_super_admin = True
        else:
            print("Admin user not found.")
        
        # 2. Update doc_numbers for historical documents
        docs = Document.query.filter(Document.doc_number == None).all()
        print(f"Found {len(docs)} documents without a doc_number.")
        
        for doc in docs:
            # Generate doc_number
            created_date = doc.created_at or datetime.now()
            today_str = created_date.strftime("%Y%m%d")
            
            # Find the highest doc_number for this day in DB
            max_doc = db.session.query(db.func.max(Document.doc_number)).filter(
                Document.doc_number.like(f"{today_str}%")
            ).scalar()
            
            if max_doc:
                try:
                    last_seq = int(max_doc[-3:])
                    doc_number = f"{today_str}{str(last_seq + 1).zfill(3)}"
                except Exception:
                    doc_number = f"{today_str}001"
            else:
                doc_number = f"{today_str}001"
                
            print(f"Assigning doc_number {doc_number} to Document ID {doc.id} ('{doc.title}')")
            doc.doc_number = doc_number
            db.session.flush() # Flush to ensure next iteration sees the new number
            
        db.session.commit()
        print("Data washing completed successfully!")

if __name__ == "__main__":
    wash()
