import sqlite3

database = 'app_data.db'

def init_db():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users
                 (userName TEXT PRIMARY KEY, password TEXT, phoneNumber TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS SystemSettings
                 (mode TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

def save_UserData(userName, password, phoneNumber):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        "INSERT INTO Users (userName, password, phoneNumber) VALUES (?, ?, ?)", 
        (userName, password, phoneNumber)
    )
    conn.commit()
    conn.close()

def get_user_by_username(userName):
    """Get a single user by their userName (ID)"""
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("SELECT * FROM Users WHERE userName = ?", (userName,))
    user = c.fetchone()
    conn.close()
    return user