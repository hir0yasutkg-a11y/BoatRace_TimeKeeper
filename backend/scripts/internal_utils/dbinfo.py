import sqlite3
import os

db_path = 'boat_race.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print(f"Tables: {tables}")
    for table in tables:
        cur.execute(f"PRAGMA table_info({table[0]})")
        print(f"Columns in {table[0]}: {cur.fetchall()}")
    conn.close()
