import os
import sys

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'sources', 'backend'))

from app import create_app
from app.models import Document, DocumentVersion
from app.extensions import db

app = create_app()
with app.app_context():
    doc = db.session.get(Document, 92)
    if not doc:
        print("Document 92 not found")
    else:
        print(f"Document 92: title='{doc.title}', status='{doc.status}', current_version_id={doc.current_version_id}")
        versions = DocumentVersion.query.filter_by(document_id=92).all()
        print(f"Versions found: {len(versions)}")
        for v in versions:
            print(f" - Version {v.id}: no={v.version_no}, created_at={v.created_at}")
