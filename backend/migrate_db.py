import sqlite3
import os

db_path = "boatrace_data.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("ALTER TABLE races ADD COLUMN scheduled_start TEXT;")
        conn.commit()
        print(f"[MIGRATION] Successfully added scheduled_start column to races table in {db_path}.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("[MIGRATION] Column already exists.")
        else:
            print(f"[MIGRATION] Error: {e}")
    conn.close()
else:
    print(f"[MIGRATION] database file not found at {db_path}")
