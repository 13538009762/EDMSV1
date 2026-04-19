import sqlite3
import os

db_path = "instance/edms.db"
if not os.path.exists(db_path):
    print("DB not found at default path, trying backup paths...")
    db_path = "edms.db"

print(f"Repairing {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 1. Create new table with correct schema (document_id is NULL)
    cursor.execute("""
    CREATE TABLE approval_flows_new (
        id INTEGER NOT NULL PRIMARY KEY, 
        document_id INTEGER, 
        rel_id INTEGER, 
        flow_type VARCHAR(32) NOT NULL, 
        status VARCHAR(32) NOT NULL, 
        current_order INTEGER, 
        created_at DATETIME, 
        updated_at DATETIME,
        FOREIGN KEY(document_id) REFERENCES documents (id)
    )
    """)

    # 2. Copy data from old to new
    # Note: rel_id might not exist in old if previous migration failed
    cursor.execute("PRAGMA table_info(approval_flows)")
    columns = [row[1] for row in cursor.fetchall()]
    
    col_str = ", ".join([c for c in columns if c != 'rel_id'])
    if 'rel_id' in columns:
        cursor.execute(f"INSERT INTO approval_flows_new ({col_str}, rel_id) SELECT {col_str}, rel_id FROM approval_flows")
    else:
        cursor.execute(f"INSERT INTO approval_flows_new ({col_str}) SELECT {col_str} FROM approval_flows")

    # 3. Drop old table
    cursor.execute("DROP TABLE approval_flows")

    # 4. Rename new table to old name
    cursor.execute("ALTER TABLE approval_flows_new RENAME TO approval_flows")

    conn.commit()
    print("Migration successful: approval_flows.document_id is now nullable.")

except Exception as e:
    conn.rollback()
    print(f"Critical error during migration: {e}")
finally:
    conn.close()
