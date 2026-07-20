import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    monthly_budget REAL DEFAULT 0,
    profile_pic TEXT
)
""")

# CATEGORIES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
""")

# EXPENSES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER,
    amount REAL NOT NULL,
    description TEXT,
    expense_date DATE NOT NULL,

    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(category_id) REFERENCES categories(id)
)
""")

# DEFAULT CATEGORIES
default_categories = [
    "Food",
    "Transport",
    "Education",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Utilities"
]

for category in default_categories:
    cursor.execute("""
        INSERT OR IGNORE INTO categories(name)
        VALUES(?)
    """, (category,))

conn.commit()
conn.close()

print("Database created successfully!")