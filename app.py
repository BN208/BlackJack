#AI wrote start of this file
from flask import Flask, send_from_directory, request, jsonify
import random

port=3000

# static_folder='.' lets Flask serve your HTML, CSS, JS, and assets directly from the current folder
app = Flask(__name__, static_folder='.', static_url_path='')

# Example game state stored in Python
deck = ['AS', 'KH', '10D', '7C', '2S', 'QD', '9H']

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# API Endpoint that JavaScript will call
@app.route('/api/draw', methods=['POST'])
def draw_card():
    card = random.choice(deck)
    # Return JSON data back to JavaScript
    return jsonify({
        'card': card,
        'image_path': f'assets/cards/IndividualCards/{card}.png'
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Replace with real user verification later
    if username and password:
        return jsonify({'success': True, 'username': username, 'balance': 100})
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(port=port, debug=True)
