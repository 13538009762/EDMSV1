from app import create_app
from app.extensions import db
from app.models import User, Document

app = create_app()
with app.app_context():
    doc = Document.query.get(81)
    if doc:
        print(f"Doc 81: Title={doc.title}, Public={doc.is_public}, Space={doc.space_id}, Deleted={doc.deleted_at}")
        owner = doc.owner
        if owner:
            print(f"Owner: {owner.login_name}, Dept ID: {owner.department_id}")
            if owner.department:
                print(f"Owner Dept: {owner.department.name} (EN: {owner.department.name_en})")
    else:
        print("Doc 81 not found")
