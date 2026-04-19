from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    res = db.session.execute(text("PRAGMA table_info(approval_flows)"))
    print("Column Info for approval_flows:")
    for row in res:
        print(row)
