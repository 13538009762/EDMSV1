from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    try:
        db.create_all()
        print("db.create_all success")
    except Exception as e:
        print(f"db.create_all failed: {e}")
