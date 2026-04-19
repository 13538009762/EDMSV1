from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("--- Fixing Database Schema ---")
    try:
        # 1. 检查并添加 approval_flows.updated_at
        db.session.execute(text("ALTER TABLE approval_flows ADD COLUMN updated_at DATETIME;"))
        print("Success: Added column 'updated_at' to 'approval_flows'")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("Notice: Column 'updated_at' already exists in 'approval_flows'")
        else:
            print(f"Error updating approval_flows: {e}")

    try:
        # 2. 检查并添加 documents.doc_number (万一也丢了)
        db.session.execute(text("ALTER TABLE documents ADD COLUMN doc_number VARCHAR(64);"))
        print("Success: Added column 'doc_number' to 'documents'")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("Notice: Column 'doc_number' already exists in 'documents'")
        else:
            print(f"Error updating documents: {e}")

    db.session.commit()
    print("Database patching finished.")
