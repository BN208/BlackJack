import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def store_password(username, password):
    file = open("account.txt", "a")
    file.write(f"{username}:{hash_password(password)}\n")
    file.close()

def verify_password(username, password):
    hashed_password = hash_password(password)
    file = open("account.txt", "r")
    for line in file:
        if username in line:
            stored_username, stored_hashed_password = line.strip().split(":")
            if stored_username == username and stored_hashed_password == hashed_password:
                file.close()
                return True
    file.close()
    return False
