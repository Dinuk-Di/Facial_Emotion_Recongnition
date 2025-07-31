# database/db.py
import sqlite3
import os
DB_PATH = r"assets\app.db"

def get_connection():
    if not os.path.exists("assets"):
        os.makedirs("assets")

    conn = sqlite3.connect(DB_PATH)
    create_users_table(conn)
    app_settings(conn)
    recommendation_history(conn)
    emotions(conn)
    apps(conn)
    return conn

def create_users_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phonenumber TEXT,
        birthday TEXT
    );
    """
    conn.execute(query)
    conn.commit()
    
def app_settings(conn):
    query = """
    CREATE TABLE IF NOT EXISTS app_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        setting_name TEXT NOT NULL,
        setting_value TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """
    conn.execute(query)
    conn.commit()

def recommendation_history(conn):
    query = """
    CREATE TABLE IF NOT EXISTS recommendation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        emotion TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        selected_previous_recommendation TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """
    conn.execute(query)
    conn.commit()

def emotions(conn):
    query = """
    CREATE TABLE IF NOT EXISTS emotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emotion TEXT NOT NULL,
        is_positive BOOLEAN NOT NULL
    );
    """
    conn.execute(query)
    conn.commit()
def apps(conn):
    query = """
    CREATE TABLE IF NOT EXISTS apps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emotion_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        category ENUM('Songs', 'Entertainment', 'SocialMedia', 'Games', 'Communication', 'Help') NOT NULL,
        app_name TEXT NOT NULL,
        app_url TEXT,
        path TEXT,
        is_local BOOLEAN NOT NULL,
        FOREIGN KEY (emotion_id) REFERENCES emotions (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """
    conn.execute(query)
    conn.commit()
    
