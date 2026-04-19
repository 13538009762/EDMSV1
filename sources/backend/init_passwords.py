from app import create_app
from app.extensions import db
from app.models.core import User

app = create_app()
with app.app_context():
    # Find users with no password
    users = User.query.filter(User.password_hash.is_(None)).all()
    print(f"Found {len(users)} users with no password.")
    
    for u in users:
        u.set_password("123")
        print(f"Set password for: {u.login_name}")
    
    db.session.commit()
    print("Done! All users now have a password (fallback '123' if empty).")
