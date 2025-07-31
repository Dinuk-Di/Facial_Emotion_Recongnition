# database/db.py
import sqlite3
import os
DB_PATH = r"D:\RuhunaNew\Academic\Research\Facial_Recog_Repo\Group_50_Repo\DesktopApp\assets\app.db"

def get_connection():
    if not os.path.exists("assets"):
        os.makedirs("assets")

    conn = sqlite3.connect(DB_PATH)
    create_users_table(conn)
    create_emotions_table(conn)
    return conn

def create_users_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        age INTEGER,
        birthday TEXT
    );
    """
    conn.execute(query)
    conn.commit()

def create_emotions_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS emotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        emotion TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        previous_recommendation TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """
    conn.execute(query)
    conn.commit()