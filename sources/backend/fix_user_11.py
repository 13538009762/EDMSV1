from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    u = User.query.get(11)
    if u:
        print(f"Fixing user 11: {u.login_name}")
        u.last_name = "何"
        u.first_name = "欢恒"
        db.session.commit()
        print("Update successful")
    else:
        print("User 11 not found")
