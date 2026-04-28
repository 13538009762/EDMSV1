from app import create_app
from app.extensions import db
from app.models import Document, User
from app.api.documents import _doc_to_summary
import json

app = create_app()
with app.app_context():
    try:
        user = User.query.filter_by(login_name='admin').first()
        docs = Document.query.filter(Document.is_template == False, Document.deleted_at == None).all()
        print(f"Testing serialization for {len(docs)} documents")
        
        items = [_doc_to_summary(d, user) for d in docs]
        res = json.dumps({"items": items})
        print(f"Serialization success: {len(res)} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
