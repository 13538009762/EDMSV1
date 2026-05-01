from app import create_app
from app.extensions import db
from app.models import User, Department

app = create_app()
with app.app_context():
    users = User.query.all()
    for u in users:
        dept_name = u.department.name if u.department else "None"
        print(f"User: {u.login_name}, Dept ID: {u.department_id}, Dept Name: {dept_name}")
