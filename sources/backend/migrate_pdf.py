from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE documents ADD COLUMN doc_type VARCHAR(32) DEFAULT 'rich_text'"))
        print("Added doc_type to documents")
    except Exception as e:
        print(f"documents table update: {e}")
        
    try:
        db.session.execute(text("ALTER TABLE document_versions ADD COLUMN file_path VARCHAR(512)"))
        print("Added file_path to document_versions")
    except Exception as e:
        print(f"document_versions table update: {e}")
        
    db.session.commit()
