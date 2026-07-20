import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if "profile_pic" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
    conn.commit()
    print("Column 'profile_pic' added successfully!")
else:
    print("Column 'profile_pic' already exists. No changes made.")

conn.close()