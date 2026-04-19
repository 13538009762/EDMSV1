from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE approval_flows ADD COLUMN rel_id INTEGER;"))
        print("Added rel_id to approval_flows")
    except Exception as e:
        print(f"rel_id logic: {e}")

    try:
        # Note: SQLite doesn't support changing NULL/NOT NULL easily with ALTER TABLE
        # But we can try to just use it as is if it was already created or modify the DDL if fresh.
        # For existing SQLite, we'd need to recreate table, but often nullability is loose in SQLite.
        pass
    except Exception as e:
        print(f"nullability logic: {e}")
    
    db.session.commit()
    print("Done")
