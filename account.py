import hashlib; import sqlite3

def hash_password(password):
    return str(hashlib.sha256(password.encode()).hexdigest())

def store_details(username, password):
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("INSERT INTO account (username, password) VALUES (?, ?)", (username, str(hash_password(password))))
    db.commit()
    db.close()

def verify_password(username, password):
    hashed_password = hash_password(password)
    username = username
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("SELECT password FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    if x is not None and str(x[0]) == hashed_password:
        db.close()
        return True
    else:
        db.close()
        return False
    
    
def check_account(username):
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("SELECT username FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    if x is not None:
        db.close()
        return False
    else:
        db.close()
        return True
