import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "dermai.db")
print(f"Connecting to DB at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT id, email, username FROM users").fetchall()
    
    print("\n--- Users in DB ---")
    if not users:
        print("No users found.")
    else:
        for u in users:
            print(f"ID: {u['id']}, Email: {u['email']}, Username: {u['username']}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
