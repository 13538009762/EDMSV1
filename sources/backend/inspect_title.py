from app import create_app
from app.extensions import db
from app.models.document import Document

app = create_app()
with app.app_context():
    doc = Document.query.get(83)
    if doc:
        print(f"Title: {doc.title}")
        print(f"Hex: {doc.title.encode('utf-8').hex()}")
        for char in doc.title:
            print(f"Char: {char}, Code: {ord(char)}")
