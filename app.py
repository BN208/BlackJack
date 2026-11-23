from flask import Flask, send_from_directory, request, jsonify, session
import account

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