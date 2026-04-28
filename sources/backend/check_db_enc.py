import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
engine = create_engine(db_url)
with engine.connect() as conn:
    res = conn.execute(text('SHOW CREATE DATABASE edms_db')).fetchone()
    print(f"Database Creation SQL: {res}")
    
    res = conn.execute(text('SHOW VARIABLES LIKE "character_set_database"')).fetchone()
    print(f"Character Set: {res}")
    
    res = conn.execute(text('SHOW VARIABLES LIKE "collation_database"')).fetchone()
    print(f"Collation: {res}")
