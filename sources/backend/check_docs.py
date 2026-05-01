from app import create_app
from app.extensions import db
from app.models.document import Document

app = create_app()
with app.app_context():
    docs = Document.query.all()
    print(f"Total documents: {len(docs)}")
    for d in docs:
        print(f"ID: {d.id}, Title: {repr(d.title)}")
