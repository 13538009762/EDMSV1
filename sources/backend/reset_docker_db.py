import os
import sys

# 必须在导入 create_app 之前设置环境变量，并使用绝对路径
base_path = r"E:\English Encoding\competition\last\edms"
db_path = os.path.join(base_path, "sources", "docker", "data", "backend", "edms.db")
os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    print(f"Targeting Database Path: {app.config['SQLALCHEMY_DATABASE_URI']}")
    admin = User.query.filter_by(login_name='admin').first()
    if not admin:
        print("Admin missing. Creating...")
        from app.models import Department
        dept = Department.query.first()
        admin = User(login_name='admin', employee_no='AD001', department_id=dept.id if dept else None)
    
    admin.is_manager = True
    admin.registration_status = 'active'
    admin.set_password('123456')
    db.session.add(admin)
    db.session.commit()
    print("Success: Admin password has been reset to 123456 in the Docker database.")
