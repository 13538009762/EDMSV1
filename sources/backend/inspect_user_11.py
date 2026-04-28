from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    u = User.query.get(11)
    if u:
        print(f"ID: {u.id}")
        print(f"Login: {u.login_name}")
        print(f"Last Name (repr): {repr(u.last_name)}")
        print(f"First Name (repr): {repr(u.first_name)}")
        print(f"Display Name: {u.display_name()}")
    else:
        print("User 11 not found")
