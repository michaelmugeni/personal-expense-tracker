import sqlite3

def init_db():

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        monthly_budget REAL DEFAULT 0,
        profile_pic TEXT
    )
    """)

    # Categories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # Expenses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category_id INTEGER,
        amount REAL NOT NULL,
        description TEXT,
        expense_date DATE,

        FOREIGN KEY(user_id)
        REFERENCES users(id),

        FOREIGN KEY(category_id)
        REFERENCES categories(id)
    )
    """)
    
     # DEFAULT CATEGORIES
    default_categories = [
        ('Food',),
        ('Transport',),
        ('Education',),
        ('Entertainment',),
        ('Shopping',),
        ('Healthcare',),
        ('Utilities',)
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO categories(name) VALUES(?)",
        default_categories
    )

    conn.commit()
    conn.close()

    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()