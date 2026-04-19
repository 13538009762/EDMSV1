from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("Checking for missing columns...")
    try:
        # Check Department table
        db.session.execute(text("ALTER TABLE departments ADD COLUMN name_en VARCHAR(256)"))
        print("Added name_en to departments table.")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("departments.name_en already exists.")
        else:
            print(f"Note (Dept): {e}")

    try:
        # Check Position table
        db.session.execute(text("ALTER TABLE positions ADD COLUMN full_name_en VARCHAR(256)"))
        print("Added full_name_en to positions table.")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("positions.full_name_en already exists.")
        else:
            print(f"Note (Pos): {e}")

    db.session.commit()
    print("Database structure is now up to date.")
