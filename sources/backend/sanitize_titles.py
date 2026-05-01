from app import create_app
from app.extensions import db
from app.models.document import Document

app = create_app()
with app.app_context():
    docs = Document.query.all()
    count = 0
    for d in docs:
        if d.title and '\ufffd' in d.title:
            d.title = d.title.replace('\ufffd', '?')
            count += 1
    db.session.commit()
    print(f"Sanitized {count} document titles.")
