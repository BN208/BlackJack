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
            is_admin INTEGER DEFAULT 0,
            approved INTEGER NOT NULL DEFAULT 1
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AppSettings (
            setting TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerStats (
            username TEXT PRIMARY KEY,
            hands_played INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            pushes INTEGER NOT NULL DEFAULT 0,
            blackjacks INTEGER NOT NULL DEFAULT 0,
            busts INTEGER NOT NULL DEFAULT 0,
            total_wagered INTEGER NOT NULL DEFAULT 0,
            net_profit INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO AppSettings (setting, value) VALUES (?, ?)",
        ("signups_enabled", "1" if signups_enabled else "0")
    )
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(Account)").fetchall()}
    if "is_admin" not in columns:
        cursor.execute("ALTER TABLE Account ADD COLUMN is_admin INTEGER DEFAULT 0")
    if "approved" not in columns:
        cursor.execute("ALTER TABLE Account ADD COLUMN approved INTEGER NOT NULL DEFAULT 1")
    db.commit()
    admin_username = os.environ.get("ADMIN_USERNAME", "").strip().lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if admin_username and admin_password:
        cursor.execute("SELECT username FROM Account WHERE username = ?", (admin_username,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE Account SET is_admin = 1, approved = 1 WHERE username = ?",
                (admin_username,)
            )
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

def new_user(username, password, approved=True):
    username = username.lower()
    try:
        db = sqlite3.connect(get_db_path())
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO Account (username, password, money, approved) VALUES (?, ?, 100, ?)",
            (username, hash_password(password), int(approved))
        )
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
        db.close()
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
    cursor.execute(
        "SELECT username, money FROM Account "
        "WHERE is_admin = 0 AND approved = 1 ORDER BY money DESC LIMIT 10"
    )
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

def is_approved(username):
    username = username.lower()
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT approved FROM Account WHERE username = ?", (username,))
    row = cursor.fetchone()
    db.close()
    return bool(row and row[0])

def approve_account(username):
    username = username.lower()
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute(
        "UPDATE Account SET approved = 1 WHERE username = ? AND is_admin = 0",
        (username,)
    )
    db.commit()
    approved = cursor.rowcount > 0
    db.close()
    return approved

def get_accounts():
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute("SELECT username, money, is_admin, approved FROM Account ORDER BY username")
    rows = cursor.fetchall()
    db.close()
    return [
        {
            "username": row[0],
            "money": row[1],
            "is_admin": bool(row[2]),
            "approved": bool(row[3])
        }
        for row in rows
    ]

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
    cursor.execute("DELETE FROM PlayerStats WHERE username = ?", (username,))
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

def get_player_stats(username):
    username = username.lower()
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()
    cursor.execute(
        "SELECT hands_played, wins, losses, pushes, blackjacks, busts, "
        "total_wagered, net_profit FROM PlayerStats WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    db.close()
    fields = (
        "hands_played", "wins", "losses", "pushes",
        "blackjacks", "busts", "total_wagered", "net_profit"
    )
    return dict(zip(fields, row or (0,) * len(fields)))

def settle_round(results):
    db = sqlite3.connect(get_db_path())
    try:
        cursor = db.cursor()
        for username, result in results.items():
            username = username.lower()
            payout = int(result["payout"])
            bet = int(result["bet"])
            emergency_bet = bool(result.get("emergency_bet", False))
            cursor.execute(
                "UPDATE Account SET money = money + ? WHERE username = ?",
                (payout, username)
            )
            if cursor.rowcount == 0:
                continue

            outcome = result["outcome"]
            cursor.execute("""
                INSERT INTO PlayerStats (
                    username, hands_played, wins, losses, pushes, blackjacks,
                    busts, total_wagered, net_profit
                ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    hands_played = hands_played + 1,
                    wins = wins + excluded.wins,
                    losses = losses + excluded.losses,
                    pushes = pushes + excluded.pushes,
                    blackjacks = blackjacks + excluded.blackjacks,
                    busts = busts + excluded.busts,
                    total_wagered = total_wagered + excluded.total_wagered,
                    net_profit = net_profit + excluded.net_profit
            """, (
                username,
                int(outcome in ("win", "blackjack")),
                int(outcome in ("loss", "bust")),
                int(outcome == "push"),
                int(result["blackjack"]),
                int(result["bust"]),
                bet,
                payout - (0 if emergency_bet else bet)
            ))
        db.commit()
    finally:
        db.close()