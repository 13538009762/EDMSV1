from app import create_app
from app.extensions import db
from app.models.notification import Notification
from datetime import datetime

app = create_app()
with app.app_context():
    try:
        nots = Notification.query.filter(
            Notification.expires_at < datetime.utcnow(),
            Notification.is_starred == False
        ).delete()
        db.session.commit()
        print(f"Cleanup success: {nots} deleted")
    except Exception as e:
        db.session.rollback()
        print(f"Cleanup failed: {e}")
