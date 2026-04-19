from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # 确保所有老用户的状态都是 active
    db.session.execute(text("UPDATE users SET registration_status = 'active' WHERE registration_status IS NULL OR registration_status = ''"))
    db.session.commit()
    print("Database users status fixed.")
