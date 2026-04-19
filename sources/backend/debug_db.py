from app import create_app
from app.extensions import db
import sqlalchemy as sa

app = create_app()
with app.app_context():
    inspector = sa.inspect(db.engine)
    print("Tables:", inspector.get_table_names())
    
    for table in ["documents", "audit_logs"]:
        if table in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(table)]
            print(f"Columns in {table}:", cols)
