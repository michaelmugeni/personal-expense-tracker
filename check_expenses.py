import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM expenses")

expenses = cursor.fetchall()

for expense in expenses:
    print(expense)

conn.close()