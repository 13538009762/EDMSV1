from app import create_app
from app.extensions import db
from app.models import User, Document

app = create_app()
with app.app_context():
    ids = [8, 18, 28, 38, 48, 81, 12, 22, 32, 42, 52]
    for id in ids:
        doc = Document.query.get(id)
        if doc:
            print(f"Doc {id}: Title={doc.title}, Template={doc.is_template}, Space={doc.space_id}, Public={doc.is_public}")
