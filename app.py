from flask import Flask, has_request_context, send_from_directory, request, jsonify, session
from flask.sessions import SecureCookieSessionInterface
from functools import wraps
import re
import secrets
import string
import time
import os
from threading import RLock
import account
from blackjack import BlackjackTable


class ForwardedProtocolSessionInterface(SecureCookieSessionInterface):
    def get_cookie_secure(self, app):
        if has_request_context():
            forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
            forwarded_proto = forwarded_proto.split(",", 1)[0].strip().lower()
            if forwarded_proto in ("http", "https"):
                return forwarded_proto == "https"
        return super().get_cookie_secure(app)


APP_DIR = os.path.dirname(os.path.abspath(__file__))
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")
app = Flask(__name__, static_folder=None)
app.session_interface = ForwardedProtocolSessionInterface()
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

SIGNUPS_ENABLED_DEFAULT = os.environ.get("SIGNUPS_ENABLED", "0").strip().lower() in ("1", "true", "yes")

account.init_db(signups_enabled=SIGNUPS_ENABLED_DEFAULT)

games = {}  # code -> { "table": BlackjackTable, "last_active": float }
ROOM_TIMEOUT = 300
games_lock = RLock()


def generate_code(length=5):
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(length))
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


def player_game_code(username):
    return next(
        (code for code, game in games.items() if username in game['table'].players),
        None
    )


def synchronized(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        with games_lock:
            return view(*args, **kwargs)
    return wrapped


def apply_pending_payouts(table):
    if table.pending_round_results:
        account.settle_round(table.pending_round_results)
        table.pending_round_results = {}
        table.payout_results = {}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        username = session.get("username")
        if not username or not account.is_admin(username):
            return jsonify({"success": False, "error": "Admin access required"}), 403
        return view(*args, **kwargs)
    return wrapped


def game_player_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        username = session.get("username")
        if username and account.is_admin(username):
            return jsonify({"success": False, "error": "Admin accounts cannot join games"}), 403
        return view(*args, **kwargs)
    return wrapped


def signups_enabled():
    return account.get_setting("signups_enabled", "0") == "1"


def account_approval_required():
    return account.get_setting("account_approval_required", "0") == "1"


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.route('/')
def home():
    return send_from_directory(APP_DIR, 'index.html')


@app.route('/client.js')
def client_script():
    return send_from_directory(APP_DIR, 'client.js', mimetype='application/javascript')


@app.route('/styles.css')
def client_styles():
    return send_from_directory(APP_DIR, 'styles.css', mimetype='text/css')


@app.route('/assets/<path:filename>')
def client_asset(filename):
    return send_from_directory(os.path.join(APP_DIR, 'assets'), filename)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Invalid login request'}), 400
    username = data.get('username')
    password = data.get('password')
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({'success': False, 'error': 'Username and password are required'}), 400
    username = username.strip()
    if len(username) > 64 or len(password) > 128:
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 400

    if account.verify_password(username, password):
        if not account.is_approved(username):
            return jsonify({
                'success': False,
                'error': 'Your account is waiting for admin approval'
            }), 403
        session.clear()
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
    if not signups_enabled():
        return jsonify({'success': False, 'error': 'Signups are disabled'}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Invalid sign-up request'}), 400
    username = data.get('username')
    password = data.get('password')

    if not isinstance(username, str) or not USERNAME_PATTERN.fullmatch(username.strip()):
        return jsonify({
            'success': False,
            'error': 'Username must be 3 to 20 characters using letters, numbers, or underscores'
        }), 400
    username = username.strip().lower()
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        return jsonify({'success': False, 'error': 'Password must be 8–128 characters'}), 400

    approval_required = account_approval_required()
    if account.new_user(username, password, approved=not approval_required):
        if approval_required:
            return jsonify({
                'success': True,
                'pending_approval': True,
                'message': 'Your account was created and is waiting for admin approval'
            }), 202
        session.clear()
        session['username'] = username.lower()
        return jsonify({
            'success': True,
            'username': username,
            'balance': 100,
            'is_admin': False
        })
    return jsonify({'success': False, 'error': 'Username already taken'}), 409


@app.route('/api/me', methods=['GET'])
def current_user():
    username = session.get('username')
    if username and account.check_existing(username) and account.is_approved(username):
        return jsonify({
            'logged_in': True,
            'username': username,
            'balance': account.check_money(username),
            'is_admin': account.is_admin(username)
        })
    return jsonify({'logged_in': False})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify(account.get_leaderboard())


@app.route('/api/me/stats', methods=['GET'])
def player_stats():
    username = session.get('username')
    if not username or not account.check_existing(username):
        return jsonify({'success': False, 'error': 'Sign in to view your stats'}), 401
    if account.is_admin(username):
        return jsonify({'success': False, 'error': 'Admin accounts do not have player stats'}), 403
    return jsonify({'success': True, 'stats': account.get_player_stats(username)})


@app.route('/api/game/create', methods=['POST'])
@synchronized
@game_player_required
def create_game():
    cleanup_games()
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to start a game'}), 401

    if player_game_code(username):
        return jsonify({'success': False, 'error': 'You are already in a game'}), 409

    code = generate_code()
    table = BlackjackTable(num_decks=6)
    table.add_player(username)
    games[code] = {'table': table, 'last_active': time.time()}

    return jsonify({'success': True, 'code': code, 'state': table.to_dict()})


@app.route('/api/game/join', methods=['POST'])
@synchronized
@game_player_required
def join_game():
    cleanup_games()
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to join a game'}), 401

    data = request.get_json()
    code = data.get('code', '').strip().upper()

    if code not in games:
        return jsonify({'success': False, 'error': 'Invalid or expired game code'}), 404

    active_code = player_game_code(username)
    if active_code and active_code != code:
        return jsonify({'success': False, 'error': 'Leave your current game before joining another'}), 409

    table = games[code]['table']
    if len(table.players) >= 5 and username not in table.players:
        return jsonify({'success': False, 'error': 'Room is full (max 5 players)'}), 403

    table.add_player(username)
    games[code]['last_active'] = time.time()

    return jsonify({'success': True, 'code': code, 'state': table.to_dict()})


@app.route('/api/game/state', methods=['GET'])
@synchronized
@game_player_required
def game_state():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'Sign in first to view this game'}), 401
    code = request.args.get('code', '').strip().upper()

    if code not in games:
        return jsonify({'success': False, 'error': 'Room closed'}), 404

    table = games[code]['table']
    if username not in table.players:
        return jsonify({'success': False, 'error': 'You are not in this game'}), 403
    games[code]['last_active'] = time.time()
    bal = account.check_money(username)
    return jsonify({'success': True, 'state': table.to_dict(), 'balance': bal})


@app.route('/api/game/bet', methods=['POST'])
@synchronized
@game_player_required
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
    if current_bal is False:
        return jsonify({'success': False, 'error': 'Account not found'}), 401
    emergency_bet = current_bal == 0 and amount == 1
    if amount > current_bal and not emergency_bet:
        return jsonify({'success': False, 'error': 'Insufficient balance'}), 400

    table = games[code]['table']
    ok, msg = table.place_bet(username, amount, emergency=emergency_bet)
    if not ok:
        return jsonify({'success': False, 'error': msg}), 400

    if not emergency_bet:
        account.update_money(username, -amount)
    apply_pending_payouts(table)
    games[code]['last_active'] = time.time()

    return jsonify({'success': True, 'state': table.to_dict(), 'balance': account.check_money(username)})


@app.route('/api/game/twist', methods=['POST'])
@synchronized
@game_player_required
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
@synchronized
@game_player_required
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
@synchronized
def leave_game():
    username = session.get('username')
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()

    if code in games and username:
        table = games[code]['table']
        seat = table.seats.get(username)
        if table.phase == "betting" and seat and seat["bet"] > 0:
            account.update_money(username, seat["bet"])
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
    return jsonify({
        "success": True,
        "accounts": account.get_accounts(),
        "signups_enabled": signups_enabled(),
        "account_approval_required": account_approval_required()
    })


@app.route('/api/admin/settings/signups', methods=['POST'])
@admin_required
def admin_set_signups():
    data = request.get_json() or {}
    enabled = data.get("enabled")
    if not isinstance(enabled, bool):
        return jsonify({"success": False, "error": "enabled must be true or false"}), 400
    account.set_setting("signups_enabled", "1" if enabled else "0")
    return jsonify({"success": True, "signups_enabled": enabled})


@app.route('/api/admin/settings/account-approval', methods=['POST'])
@admin_required
def admin_set_account_approval():
    data = request.get_json() or {}
    enabled = data.get("enabled")
    if not isinstance(enabled, bool):
        return jsonify({"success": False, "error": "enabled must be true or false"}), 400
    account.set_setting("account_approval_required", "1" if enabled else "0")
    return jsonify({"success": True, "account_approval_required": enabled})


@app.route('/api/admin/accounts/<username>/approve', methods=['POST'])
@admin_required
def admin_approve_account(username):
    username = username.strip().lower()
    if not account.check_existing(username):
        return jsonify({"success": False, "error": "Account not found"}), 404
    if account.is_admin(username):
        return jsonify({"success": False, "error": "Admin accounts do not require approval"}), 400
    if not account.approve_account(username):
        return jsonify({"success": False, "error": "Account could not be approved"}), 404
    return jsonify({"success": True, "username": username})


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