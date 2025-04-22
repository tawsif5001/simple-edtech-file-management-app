import sqlite3
from werkzeug.security import generate_password_hash

def setup_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # ✅ Create admin table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # ✅ Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # ✅ Insert one admin manually
    admin_email = 'admin@example.com'
    admin_password = generate_password_hash('admin123', method='pbkdf2:sha256')
    try:
        cursor.execute('INSERT INTO admin (email, password) VALUES (?, ?)', (admin_email, admin_password))
    except sqlite3.IntegrityError:
        print('Admin already exists')

    conn.commit()
    conn.close()
    print('Database initialized.')

if __name__ == '__main__':
    setup_database()





