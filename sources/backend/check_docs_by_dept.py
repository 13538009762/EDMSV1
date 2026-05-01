from app import create_app
from app.extensions import db
from app.models import Document, User, Department

app = create_app()
with app.app_context():
    # Check all departments and document counts
    depts = Department.query.all()
    for d in depts:
        count = Document.query.join(User).filter(User.department_id == d.id, Document.space_id == None).count()
        print(f"Dept ID: {d.id}, Name: {d.name}, EN: {d.name_en}, Doc Count: {count}")

    # Check documents for HR specifically
    hr_docs = Document.query.join(User).filter(User.department_id == 3).all()
    print(f"\nHR Documents (Dept ID 3):")
    for doc in hr_docs:
        print(f"ID: {doc.id}, Title: {doc.title}, Owner: {doc.owner.login_name if doc.owner else 'None'}")
