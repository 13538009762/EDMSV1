from app import create_app
from app.extensions import db
from app.models import User, Department, Position

app = create_app()
with app.app_context():
    user_count = db.session.query(User).count()
    manager_count = db.session.query(User).filter(User.is_manager == True).count()
    users = db.session.query(User).limit(10).all()
    departments = db.session.query(Department).count()
    positions = db.session.query(Position).count()
    
    ruk = db.session.query(User).filter(User.login_name == 'ruk1').first()
    print(f"ruk1 exists: {ruk is not None}")
    if ruk:
        print(f"ruk1 details: manager={ruk.is_manager}, employee_no={ruk.employee_no}, name={ruk.display_name()}")
    
    admins = db.session.query(User).filter(User.is_manager == True).all()
    print(f"Managers count: {len(admins)}")
    print("Manager list:")
    for a in admins[:5]:
        print(f"  - {a.login_name}")

