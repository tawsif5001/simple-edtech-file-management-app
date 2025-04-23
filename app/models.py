import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def add_subject(user_id, name):
    conn = get_db_connection()
    conn.execute('INSERT INTO subjects (user_id, name) VALUES (?, ?)', (user_id, name))
    conn.commit()
    conn.close()

def get_subjects_for_user(user_id):
    conn = get_db_connection()
    subjects = conn.execute('SELECT * FROM subjects WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return subjects
