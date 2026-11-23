from flask import Flask, send_from_directory, request, jsonify, session
from functools import wraps
import random
import string
import time
import os
import account
from blackjack import BlackjackTable

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get("BLACKJACK_SECRET_KEY")
if not app.secret_key:
    app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("BLACKJACK_SECRET_KEY must be set")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0").strip().lower() in ("1", "true", "yes")
)

SIGNUPS_ENABLED = os.environ.get("SIGNUPS_ENABLED", "0").strip().lower() in ("1", "true", "yes")

account.init_db()

games = {}  # code -> { "table": BlackjackTable, "last_active": float }
ROOM_TIMEOUT = 300


def generate_code(length=5):
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if code not in games:
            return code


def cleanup_games():
    now = time.time()
    expired = [
        code for code, g in games.items()
        if not g['table'].players or (now - g['last_active'] > ROOM_TIMEOUT)
    ]
    for code in expired:
        del games[code]


def apply_pending_payouts(table):
    if hasattr(table, 'payout_results') and table.payout_results:
        for username, payout in table.payout_results.items():
            account.update_money(username, payout)
        table.payout_results = {}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        username = session.get("username")
        if not username or not account.is_admin(username):
            return jsonify({"success": False, "error": "Admin access required"}), 403
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


@app.route('/admin')
def admin_console():
    return send_from_directory('.', 'index.html')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if account.verify_password(username, password):
        session['username'] = username.lower()
        balance = account.check_money(username)
        return jsonify({
            'success': True,
            'username': username.lower(),
            'balance': balance,
            'is_admin': account.is_admin(username)
        })
    return jsonify({'success': False, 'error': 'Invalid username or password'}), 401


@app.route('/api/signup', methods=['POST'])
def signup():
    if not SIGNUPS_ENABLED:
        return jsonify({'success': False, 'error': 'Signups are disabled'}), 403
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
            'balance': account.check_money(username),
            'is_admin': account.is_admin(username)
        })
    return jsonify({'logged_in': False})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})


@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify(account.get_leaderboard())


@app.route('/api/game/create', methods=['POST'])
def create_game():
    cleanup_games()
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to start a game'}), 401

    code = generate_code()
    table = BlackjackTable(num_decks=6)
    table.add_player(username)
    games[code] = {'table': table, 'last_active': time.time()}

    return jsonify({'success': True, 'code': code, 'state': table.to_dict()})


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

    table = games[code]['table']
    if len(table.players) >= 5 and username not in table.players:
        return jsonify({'success': False, 'error': 'Room is full (max 5 players)'}), 403

    table.add_player(username)
    games[code]['last_active'] = time.time()

    return jsonify({'success': True, 'code': code, 'state': table.to_dict()})


@app.route('/api/game/state', methods=['GET'])
def game_state():
    username = session.get('username')
    code = request.args.get('code', '').strip().upper()

    if code not in games:
        return jsonify({'success': False, 'error': 'Room closed'}), 404

    table = games[code]['table']
    bal = account.check_money(username) if username else 0
    return jsonify({'success': True, 'state': table.to_dict(), 'balance': bal})


@app.route('/api/game/bet', methods=['POST'])
def place_bet():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    code = data.get('code', '').strip().upper()
    try:
        amount = int(data.get('amount', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Invalid bet amount'}), 400

    if code not in games:
        return jsonify({'success': False, 'error': 'Room not found'}), 404

    if amount <= 0:
        return jsonify({'success': False, 'error': 'Bet must be at least £1'}), 400

    current_bal = account.check_money(username)
    if amount > current_bal:
        return jsonify({'success': False, 'error': 'Insufficient balance'}), 400

    table = games[code]['table']
    ok, msg = table.place_bet(username, amount)
    if not ok:
        return jsonify({'success': False, 'error': msg}), 400

    new_bal = account.update_money(username, -amount)
    apply_pending_payouts(table)
    games[code]['last_active'] = time.time()

    return jsonify({'success': True, 'state': table.to_dict(), 'balance': account.check_money(username)})


@app.route('/api/game/twist', methods=['POST'])
def game_twist():
    username = session.get('username')
    data = request.get_json()
    code = data.get('code', '').strip().upper()

    if code not in games or not username:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    table = games[code]['table']
    ok, msg = table.twist(username)
    if not ok:
        return jsonify({'success': False, 'error': msg}), 400

    apply_pending_payouts(table)
    games[code]['last_active'] = time.time()

    return jsonify({'success': True, 'state': table.to_dict(), 'balance': account.check_money(username)})


@app.route('/api/game/stick', methods=['POST'])
def game_stick():
    username = session.get('username')
    data = request.get_json()
    code = data.get('code', '').strip().upper()

    if code not in games or not username:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    table = games[code]['table']
    ok, msg = table.stick(username)
    if not ok:
        return jsonify({'success': False, 'error': msg}), 400

    apply_pending_payouts(table)
    games[code]['last_active'] = time.time()

    return jsonify({'success': True, 'state': table.to_dict(), 'balance': account.check_money(username)})


@app.route('/api/game/leave', methods=['POST'])
def leave_game():
    username = session.get('username')
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()

    if code in games and username:
        table = games[code]['table']
        table.remove_player(username)
        apply_pending_payouts(table)
        if len(table.players) == 0:
            del games[code]
        else:
            games[code]['last_active'] = time.time()

    return jsonify({'success': True})


@app.route('/api/admin/accounts', methods=['GET'])
@admin_required
def admin_accounts():
    return jsonify({"success": True, "accounts": account.get_accounts(), "signups_enabled": SIGNUPS_ENABLED})


@app.route('/api/admin/accounts/money', methods=['POST'])
@admin_required
def admin_set_money():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()
    try:
        amount = int(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid balance"}), 400
    if amount < 0:
        return jsonify({"success": False, "error": "Balance cannot be negative"}), 400
    if not account.check_existing(username):
        return jsonify({"success": False, "error": "Account not found"}), 404
    balance = account.set_money(username, amount)
    return jsonify({"success": True, "username": username, "balance": balance})


@app.route('/api/admin/accounts/<username>', methods=['DELETE'])
@admin_required
def admin_delete_account(username):
    username = username.strip().lower()
    if username == session.get("username"):
        return jsonify({"success": False, "error": "Cannot delete the active admin account"}), 400
    if not account.check_existing(username):
        return jsonify({"success": False, "error": "Account not found"}), 404
    account.delete_account(username)
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")), debug=False)