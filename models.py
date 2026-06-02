from flask_login import UserMixin
import sqlite3

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(id=user_data[0], username=user_data[1], password=user_data[2])
        return None

    @staticmethod
    def find_by_username(username):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(id=user_data[0], username=user_data[1], password=user_data[2])
        return None

    @staticmethod
    def create(username, password):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return User(id=user_id, username=username, password=password)
        except sqlite3.IntegrityError:
            conn.close()
            return None

    @staticmethod
    def get_user_history(user_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'user_id': row[1],
                'image_path': row[2],
                'species': row[3],
                'length': row[4],
                'weight': row[5],
                'timestamp': row[6]
            })
        return history

class History:
    @staticmethod
    def save_prediction(user_id, image_path, species, length, weight):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (user_id, image_path, species, length, weight)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, image_path, species, length, weight))
        conn.commit()
        conn.close()

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            species TEXT NOT NULL,
            length REAL NOT NULL,
            weight REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()
