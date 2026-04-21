import sqlite3

def init_db():
    conn = sqlite3.connect('schedule.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    reated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
    conn.commit()
    conn.close()

def save_user(user_id, username, first_name):
    conn = sqlite3.connect('schedule.db')
    cur = conn.cursor()
    cur.execute("""
    INSERT OR IGNORE INTO users (user_id, username, first_name)
    VALUES (?, ?, ?)
""", (user_id, username, first_name))
    conn.commit()
    conn.close()