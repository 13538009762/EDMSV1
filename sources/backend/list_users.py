from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print("Listing all active users:")
    for u in users:
        print(f"ID: {u.id}, Login: {u.login_name}, Name: {u.last_name} {u.first_name}, Status: {u.registration_status}")
