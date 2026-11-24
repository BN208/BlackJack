import sqlite3
import os
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash


def get_db_path():
    path = os.environ.get("BLACKJACK_DB", "account.db")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    return path

def init_db(signups_enabled=False):
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Account (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            money INTEGER DEFAULT 100,
            is_admin INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AppSettings (
            setting TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO AppSettings (setting, value) VALUES (?, ?)",
        ("signups_enabled", "1" if signups_enabled else "0")
    )
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(Account)").fetchall()}
    if "is_admin" not in columns:
        cursor.execute("ALTER TABLE Account ADD COLUMN is_admin INTEGER DEFAULT 0")
    db.commit()
    admin_username = os.environ.get("ADMIN_USERNAME", "").strip().lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if admin_username and admin_password:
        cursor.execute("SELECT username FROM Account WHERE username = ?", (admin_username,))
        if cursor.fetchone():
            cursor.execute("UPDATE Account SET is_admin = 1 WHERE username = ?", (admin_username,))
        else:
            cursor.execute(
                "INSERT INTO Account (username, password, money, is_admin) VALUES (?, ?, 100, 1)",
                (admin_username, hash_password(admin_password))
            )
        db.commit()
    db.close()

def hash_password(password):
    return generate_password_hash(password)

def check_existing(username):
    username = username.lower()
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT username FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    db.close()
    return x is not None

def new_user(username, password):
    username = username.lower()
    if not check_existing(username):
        db = sqlite3.connect(get_db_path())
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
        db = sqlite3.connect(get_db_path())
        cursor = db.cursor()
        cursor.execute("SELECT password FROM Account WHERE username = ?", (username,))
        x = cursor.fetchone()
        if not x:
            db.close()
            return False

        stored = str(x[0])
        if len(stored) == 64:
            matches = stored == hashlib.sha256(password.encode()).hexdigest()
            if matches:
                cursor.execute(
                    "UPDATE Account SET password = ? WHERE username = ?",
                    (generate_password_hash(password), username)
                )
                db.commit()
        else:
            matches = check_password_hash(stored, password)
        db.close()
        return matches
    return False

def check_money(username):
    username = username.lower()
    if not check_existing(username):
        return False
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT money FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    db.close()
    return x[0]

def update_money(username, delta):
    username = username.lower()
    if not check_existing(username):
        return False
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("UPDATE Account SET money = money + ? WHERE username = ?", (int(delta), username))
    db.commit()
    cursor.execute("SELECT money FROM Account WHERE username = ?", (username,))
    new_bal = cursor.fetchone()[0]
    db.close()
    return new_bal

def get_leaderboard():
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT username, money FROM Account ORDER BY money DESC LIMIT 10")
    rows = cursor.fetchall()
    db.close()
    return [{"username": r[0], "money": r[1]} for r in rows]

def is_admin(username):
    username = username.lower()
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM Account WHERE username = ?", (username,))
    row = cursor.fetchone()
    db.close()
    return bool(row and row[0])

def get_accounts():
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT username, money, is_admin FROM Account ORDER BY username")
    rows = cursor.fetchall()
    db.close()
    return [{"username": row[0], "money": row[1], "is_admin": bool(row[2])} for row in rows]

def set_money(username, amount):
    username = username.lower()
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("UPDATE Account SET money = ? WHERE username = ?", (int(amount), username))
    db.commit()
    db.close()
    return int(amount)

def delete_account(username):
    username = username.lower()
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("DELETE FROM Account WHERE username = ?", (username,))
    db.commit()
    db.close()

def get_setting(setting, default=None):
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT value FROM AppSettings WHERE setting = ?", (setting,))
    row = cursor.fetchone()
    db.close()
    return row[0] if row else default

def set_setting(setting, value):
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO AppSettings (setting, value) VALUES (?, ?) "
        "ON CONFLICT(setting) DO UPDATE SET value = excluded.value",
        (setting, str(value))
    )
    db.commit()
    db.close()