from app import create_app
from app.extensions import db
from app.models.notification import Notification
from app.models.core import User

app = create_app()
with app.app_context():
    try:
        user = User.query.filter_by(login_name='admin').first()
        if not user:
            print("Admin user not found")
        else:
            print(f"Checking notifications for user {user.id}")
            nots = Notification.query.filter_by(user_id=user.id).all()
            print(f"Found {len(nots)} notifications")
            for n in nots:
                print(f"NID: {n.id}, Type: {n.type}, Title: {n.title}")
                print(n.to_dict())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
