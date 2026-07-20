import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if "monthly_budget" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN monthly_budget REAL DEFAULT 0")
    conn.commit()
    print("Column 'monthly_budget' added successfully!")
else:
    print("Column 'monthly_budget' already exists. No changes made.")

conn.close()