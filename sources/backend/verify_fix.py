from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    u = User.query.get(11)
    if u:
        print(f"User 11 Login: {u.login_name}")
        print(f"User 11 Last Name (UTF-8 bytes): {u.last_name.encode('utf-8')}")
        print(f"User 11 First Name (UTF-8 bytes): {u.first_name.encode('utf-8')}")
