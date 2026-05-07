from app import create_app
from app.extensions import db
from app.models.document import Document
from app.models.core import User, Department
from sqlalchemy import func

app = create_app()
with app.app_context():
    total = Document.query.count()
    public = Document.query.filter_by(is_public=True).count()
    
    # Check user 'hhh'
    user_hhh = User.query.filter_by(login_name='hhh').first()
    if user_hhh:
        hhh_owned = Document.query.filter_by(owner_id=user_hhh.id).count()
        
        # Check department docs
        dept_docs = 0
        if user_hhh.department_id:
            dept_docs = Document.query.join(User, Document.owner_id == User.id)\
                .filter(User.department_id == user_hhh.department_id).count()
        
        print(f"User: hhh (ID: {user_hhh.id})")
        print(f"Total System Documents: {total}")
        print(f"Public Documents: {public}")
        print(f"hhh Owned Documents: {hhh_owned}")
        print(f"hhh Department Documents: {dept_docs}")
    else:
        print("User 'hhh' not found.")
