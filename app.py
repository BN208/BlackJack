from flask import Flask, send_from_directory, request, jsonify, session; import account; import random; import string; import time

port = 3000
app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = "change-this-to-any-random-secret-string"  # Encrypts session cookies

account.init_db()

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if account.verify_password(username, password):
        session['username'] = username.lower()
        balance = account.check_money(username)
        return jsonify({'success': True, 'username': username.lower(), 'balance': balance})
    return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

    if account.new_user(username, password):
        session['username'] = username.lower()
        return jsonify({'success': True, 'username': username.lower(), 'balance': 100})
    return jsonify({'success': False, 'error': 'Username already taken'}), 409

@app.route('/api/me', methods=['GET'])
def current_user():
    username = session.get('username')
    if username and account.check_existing(username):
        return jsonify({
            'logged_in': True,
            'username': username,
            'balance': account.check_money(username)
        })
    return jsonify({'logged_in': False})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify(account.get_leaderboard())

if __name__ == '__main__':
    app.run(port=port, debug=True)

games = {}  # Stores active rooms: { "AB12C": { "host": "ben", "players": ["ben"] } }

def generate_code(length=5):
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if code not in games:
            return code

@app.route('/api/game/create', methods=['POST'])
def create_game():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to start a game'}), 401

    code = generate_code()
    games[code] = {
        'host': username,
        'players': [username]
    }
    return jsonify({'success': True, 'code': code})

@app.route('/api/game/join', methods=['POST'])
def join_game():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to join a game'}), 401

    data = request.get_json()
    code = data.get('code', '').strip().upper()

    if code not in games:
        return jsonify({'success': False, 'error': 'Invalid game code'}), 404

    if username not in games[code]['players']:
        games[code]['players'].append(username)

    return jsonify({'success': True, 'code': code, 'players': games[code]['players']})


ROOM_TIMEOUT = 300  # 5 minutes of inactivity

def cleanup_games():
    now = time.time()
    expired = [
        code for code, g in games.items()
        if not g['players'] or (now - g['last_active'] > ROOM_TIMEOUT)
    ]
    for code in expired:
        del games[code]

@app.route('/api/game/create', methods=['POST'])
def create_game():
    cleanup_games()
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to start a game'}), 401

    code = generate_code()
    games[code] = {
        'host': username,
        'players': [username],
        'last_active': time.time()
    }
    return jsonify({'success': True, 'code': code})

@app.route('/api/game/join', methods=['POST'])
def join_game():
    cleanup_games()
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to join a game'}), 401

    data = request.get_json()
    code = data.get('code', '').strip().upper()

    if code not in games:
        return jsonify({'success': False, 'error': 'Invalid or expired game code'}), 404

    if username not in games[code]['players']:
        games[code]['players'].append(username)
    games[code]['last_active'] = time.time()

    return jsonify({'success': True, 'code': code, 'players': games[code]['players']})

@app.route('/api/game/leave', methods=['POST'])
def leave_game():
    username = session.get('username')
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()

    if code in games and username in games[code]['players']:
        games[code]['players'].remove(username)
        # Immediately delete the room if nobody is left
        if len(games[code]['players']) == 0:
            del games[code]
        else:
            # Reassign host if the original host left
            games[code]['host'] = games[code]['players'][0]
            games[code]['last_active'] = time.time()

    return jsonify({'success': True})