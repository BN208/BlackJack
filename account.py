import hashlib; import sqlite3

def hash_password(password):
    return str(hashlib.sha256(password.encode()).hexdigest())

def check_existing(username):
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("SELECT username FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    if x is not None:
        db.close()
        return True
    db.close()
    return False

def new_user(username, password):
    if check_existing(username) == False:
        db = sqlite3.connect("account.db")
        cursor = db.cursor()
        cursor.execute("INSERT INTO account (username, password) VALUES (?, ?)", (username, str(hash_password(password))))
        db.commit()
        db.close()
        return True
    return False
    
def verify_password(username, password): #checks if password is correct compared to username
    if check_existing(username) == True:
        hashed_password = hash_password(password)
        username = username
        db = sqlite3.connect("account.db")
        cursor = db.cursor()
        cursor.execute("SELECT password FROM Account WHERE username = ?", (username,))
        x = cursor.fetchone()
        if x is not None and str(x[0]) == hashed_password:
            db.close()
            return True
        db.close()
        return False
    return False
    
def check_money(username):
    if check_existing(username) == False:
        return False
    db = sqlite3.connect("account.db")
    cursor = db.cursor()
    cursor.execute("SELECT money FROM Account WHERE username = ?", (username,))
    x = cursor.fetchone()
    return x[0]

