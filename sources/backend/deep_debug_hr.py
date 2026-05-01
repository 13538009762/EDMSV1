from app import create_app
from app.extensions import db
from app.models import User, Document, Department
from sqlalchemy import or_

app = create_app()
with app.app_context():
    dpt = Department.query.get(3)
    user = User.query.filter_by(login_name='admin').first()
    
    print(f"Checking Dept {dpt.id}: {dpt.name}")
    
    # Try the exact same query as list_document_tree
    q = Document.query.join(User).filter(
        User.department_id == dpt.id,
        Document.space_id == None,
        Document.is_template == False,
        Document.deleted_at == None,
        or_(
            Document.owner_id == user.id,
            Document.is_public == True
        )
    )
    print(f"Query: {q}")
    docs = q.all()
    print(f"Found {len(docs)} documents")
    for d in docs:
        print(f"  - {d.id}: {d.title}")
        
    # Check if doc 81 is in the system
    doc81 = Document.query.get(81)
    if doc81:
        print(f"\nDoc 81 details:")
        print(f"  Owner ID: {doc81.owner_id}")
        print(f"  Owner Dept ID: {doc81.owner.department_id if doc81.owner else 'No Owner'}")
        print(f"  Is Public: {doc81.is_public}")
        print(f"  Is Template: {doc81.is_template}")
        print(f"  Space ID: {doc81.space_id}")
        print(f"  Deleted: {doc81.deleted_at}")
