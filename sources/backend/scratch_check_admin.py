from app import create_app
from app.extensions import db
from app.models import User, Department

app = create_app()
with app.app_context():
    # Because we're calling create_app(), the bootstrap logic in app/__init__.py should have run!
    admin = User.query.filter_by(login_name='admin').first()
    if admin:
        print(f"User 'admin' exists.")
        print(f"ID: {admin.id}")
        print(f"Is Manager: {admin.is_manager}")
        print(f"Status: {admin.registration_status}")
        # Verify password
        correct = admin.check_password('123456')
        print(f"Password '123456' is correct: {correct}")
        
        if not correct:
            print("Fixing password...")
            admin.set_password('123456')
            db.session.commit()
            print("Password fixed.")
    else:
        print("User 'admin' does NOT exist even after create_app() bootstrap!")
