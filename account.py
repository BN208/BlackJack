import hashlib
import sqlite3

def init_db():
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Account (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            money INTEGER DEFAULT 100
        )
    """)
    db.commit()
    db.close()

def hash_password(password):
    return str(hashlib.sha256(password.encode()).hexdigest())

def check_existing(username):
    username = username.lower()
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("SELECT username FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    db.close()
    return x is not None

def new_user(username, password):
    username = username.lower()
    if not check_existing(username):
        db = sqlite3.connect("account.db")
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO Account (username, password, money) VALUES (?, ?, 100)",
            (username, hash_password(password))
        )
        db.commit()
        db.close()
        return True
    return False

def verify_password(username, password):
    username = username.lower()
    if check_existing(username):
        hashed_password = hash_password(password)
        db = sqlite3.connect("account.db")
        cursor = db.cursor()
        cursor.execute("SELECT password FROM Account WHERE username = ?", (username,))
        x = cursor.fetchone()
        db.close()
        return x is not None and str(x[0]) == hashed_password
    return False

def check_money(username):
    username = username.lower()
    if not check_existing(username):
        return False
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("SELECT money FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    db.close()
    return x[0]

def get_leaderboard():
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("SELECT username, money FROM Account ORDER BY money DESC LIMIT 10")
    rows = cursor.fetchall()
    db.close()
    return [{"username": r[0], "money": r[1]} for r in rows]