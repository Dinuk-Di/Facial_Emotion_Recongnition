# database/db.py
import sqlite3
import os
from typing import List, Tuple
DB_PATH = r"assets\app.db"

def initialize_db():
    if not os.path.exists("assets"):
        os.makedirs("assets")

    conn = sqlite3.connect(DB_PATH)
    create_users_table(conn)
    app_settings(conn)
    recommendation_history(conn)
    emotions(conn)
    apps(conn)
    add_emotions(conn)
    return conn

def get_connection():
    if not os.path.exists(DB_PATH):
        initialize_db()
    return sqlite3.connect(DB_PATH)

def create_users_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        phonenumber TEXT,
        birthday TEXT,
        session_id TEXT
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
        category TEXT NOT NULL CHECK(category IN (
            'Songs', 'Entertainment', 'SocialMedia', 'Games', 'Communication', 'Help', 'Other')),
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

    
# Add emotion function
def add_emotions(conn):
    emotions_data = [
        ("ANGRY", False),
        ("BOARING", False),
        ("DISGUST", False),
        ("FEAR", False),
        ("HAPPY", True),
        ("NEUTRAL", True),
        ("SAD", False),
        ("STRESS", False),
        ("SURPRISE", True),
    ]

    cursor = conn.cursor()
    for emotion, is_positive in emotions_data:
        cursor.execute("INSERT INTO emotions (emotion, is_positive) VALUES (?, ?)", (emotion, is_positive))
    conn.commit()

def add_app_data(conn, user_id, category, app_name, app_url, path, is_local, selected_emotions):
    """
    Inserts app entries for all selected emotions.

    :param conn: SQLite connection
    :param user_id: ID of the user
    :param category: App category (must match table constraint)
    :param app_name: Name of the application
    :param app_url: App URL (can be None)
    :param path: Path to the application (can be None)
    :param is_local: Boolean, whether the path is local
    :param selected_emotions: List of emotion names (strings)
    """

    cursor = conn.cursor()
    if path and not path.endswith("\\"):
        path += "\\"
    path += app_name + ".exe"
    # Fetch emotion_id for each emotion name
    emotion_ids = []
    for emotion in selected_emotions:
        cursor.execute("SELECT id FROM emotions WHERE emotion = ?", (emotion,))
        result = cursor.fetchone()
        if result:
            emotion_ids.append(result[0])
        else:
            print(f"[Warning] Emotion '{emotion}' not found in table.")

    # Insert app entry for each emotion_id
    for emotion_id in emotion_ids:
        cursor.execute("""
            INSERT INTO apps (emotion_id, user_id, category, app_name, app_url, path, is_local)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (emotion_id, user_id, category, app_name, app_url, path, is_local))

    conn.commit()
def get_apps_by_emotion(conn, emotion: str) -> List[Tuple]:
    """
    Fetches apps associated with a specific emotion.

    :param conn: SQLite connection
    :param emotion: Emotion name
    :return: List of app entries (tuples)
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.category, a.app_name, a.app_url, a.path, a.is_local
        FROM apps a
        JOIN emotions e ON a.emotion_id = e.id
        WHERE e.emotion = ?
    """, (emotion,))
    all_data = cursor.fetchall()
    # get name, category and path only
    filtered_data = [(row[2], row[1], row[4]) for row in all_data]
    return filtered_data


# main 
if __name__ == "__main__":
    conn = get_connection()
    apps_list = get_apps_by_emotion(conn, "Stress")
    for app in apps_list:
        print(app)
    conn.close()
