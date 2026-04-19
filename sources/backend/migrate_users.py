from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128);"))
        print("Set password_hash")
    except Exception as e:
        print(f"p_hash already there: {e}")

    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN registration_status VARCHAR(32) DEFAULT 'active';"))
        print("Set registration_status")
    except Exception as e:
        print(f"status already there: {e}")
    
    db.session.commit()
