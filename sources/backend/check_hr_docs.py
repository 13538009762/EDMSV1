from app import create_app
from app.extensions import db
from app.models import Document, User, Department

app = create_app()
with app.app_context():
    hr_docs = Document.query.join(User).filter(User.department_id == 3).all()
    print(f"HR Documents (Dept ID 3):")
    for doc in hr_docs:
        print(f"ID: {doc.id}, Title: {doc.title}, Owner: {doc.owner.login_name}, Public: {doc.is_public}, Space ID: {doc.space_id}")
