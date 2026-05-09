import sys
import os

# Add sources/backend to path
backend_path = os.path.join(os.getcwd(), "sources", "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app import create_app
from app.extensions import db
from app.models.core import User, Department
from sqlalchemy import func

app = create_app()
with app.app_context():
    total = User.query.count()
    active = User.query.filter_by(registration_status='active').count()
    pending = User.query.filter(User.registration_status != 'active').count()
    
    print("-" * 30)
    print(f"DATABASE DIAGNOSTICS")
    print(f"Total Users: {total}")
    print(f"Active Users: {active}")
    print(f"Pending/Other: {pending}")
    
    depts = db.session.query(Department.name, func.count(User.id))\
        .join(User, User.department_id == Department.id)\
        .group_by(Department.name).all()
    
    print("\nUsers per Department:")
    for name, count in depts:
        print(f" - {name}: {count}")
        
    admin_user = User.query.filter(func.lower(User.login_name) == 'admin').first()
    if admin_user:
        print(f"\nAdmin Found: {admin_user.login_name} (Dept ID: {admin_user.department_id})")
        # Check if login_name is exactly 'admin'
        print(f"Exact match for 'admin': {admin_user.login_name == 'admin'}")
    else:
        print("\nCRITICAL: No user with login 'admin' found!")
        # List first 5 users to see what's there
        print("\nFirst 5 users in DB:")
        for u in User.query.limit(5).all():
            print(f" - {u.login_name} ({u.registration_status})")
    print("-" * 30)
