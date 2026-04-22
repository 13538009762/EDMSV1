from dotenv import load_dotenv
load_dotenv()
from app import create_app
from app.extensions import db
from app.models import Department, User

app = create_app()
with app.app_context():
    try:
        dept = Department(name='test', code='T')
        db.session.add(dept)
        db.session.flush()
        admin = User(login_name='admin', employee_no='ADMIN001', first_name='S', last_name='A', department_id=dept.id, is_manager=True)
        db.session.add(admin)
        db.session.commit()
        print('Success')
    except Exception as e:
        print('ERROR:', type(e), str(e))
        if hasattr(e, 'orig'):
            print('ORIGINAL:', e.orig)
