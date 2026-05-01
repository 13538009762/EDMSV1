from app import create_app
from app.extensions import db
from app.models import User, Document, Department
from sqlalchemy import or_

app = create_app()
with app.app_context():
    # Simulate admin user
    user = User.query.filter_by(login_name='admin').first()
    
    depts = Department.query.all()
    print(f"Total departments in DB: {len(depts)}")
    
    for dpt in depts:
        docs = Document.query.join(User).filter(
            User.department_id == dpt.id,
            Document.space_id == None,
            Document.is_template == False,
            Document.deleted_at == None,
            or_(
                Document.owner_id == user.id,
                Document.is_public == True
            )
        ).all()
        
        print(f"Dept: {dpt.name} (EN: {dpt.name_en}), Visible Docs Count: {len(docs)}")
