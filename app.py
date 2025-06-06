# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize database
def init_db():
    conn = sqlite3.connect('messenger.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, 
                 username TEXT UNIQUE, 
                 password TEXT)''')
    
    # Create messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id TEXT PRIMARY KEY,
                 sender_id TEXT,
                 receiver_id TEXT,
                 content TEXT,
                 timestamp DATETIME,
                 FOREIGN KEY(sender_id) REFERENCES users(id),
                 FOREIGN KEY(receiver_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_user_by_username(username):
    conn = sqlite3.connect('messenger.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(username, password):
    conn = sqlite3.connect('messenger.db')
    c = conn.cursor()
    user_id = str(uuid.uuid4())
    hashed_password = generate_password_hash(password)
    c.execute('INSERT INTO users VALUES (?, ?, ?)', 
              (user_id, username, hashed_password))
    conn.commit()
    conn.close()
    return user_id

def get_all_users_except(current_user_id):
    conn = sqlite3.connect('messenger.db')
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE id != ?', (current_user_id,))
    users = c.fetchall()
    conn.close()
    return [{'id': user[0], 'username': user[1]} for user in users]

def save_message(sender_id, receiver_id, content):
    conn = sqlite3.connect('messenger.db')
    c = conn.cursor()
    message_id = str(uuid.uuid4())
    timestamp = datetime.now()
    c.execute('INSERT INTO messages VALUES (?, ?, ?, ?, ?)',
              (message_id, sender_id, receiver_id, content, timestamp))
    conn.commit()
    conn.close()
    return message_id

def get_messages_between_users(user1_id, user2_id):
    conn = sqlite3.connect('messenger.db')
    c = conn.cursor()
    c.execute('''SELECT m.content, m.timestamp, u.username 
                 FROM messages m
                 JOIN users u ON m.sender_id = u.id
                 WHERE (m.sender_id = ? AND m.receiver_id = ?)
                 OR (m.sender_id = ? AND m.receiver_id = ?)
                 ORDER BY m.timestamp''',
              (user1_id, user2_id, user2_id, user1_id))
    messages = c.fetchall()
    conn.close()
    return [{'content': msg[0], 'timestamp': msg[1], 'sender': msg[2]} for msg in messages]

# Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if get_user_by_username(username):
            return render_template('register.html', error='Username already exists')
        
        create_user(username, password)
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = get_user_by_username(username)
        if not user or not check_password_hash(user[2], password):
            return render_template('login.html', error='Invalid username or password')
        
        session['user_id'] = user[0]
        session['username'] = user[1]
        return redirect(url_for('home'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/users')
def api_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    users = get_all_users_except(session['user_id'])
    return jsonify(users)

@app.route('/api/messages/<receiver_id>', methods=['GET', 'POST'])
def api_messages(receiver_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'POST':
        content = request.json.get('content')
        if not content:
            return jsonify({'error': 'No content provided'}), 400
        
        save_message(session['user_id'], receiver_id, content)
        return jsonify({'status': 'success'})
    
    else:
        messages = get_messages_between_users(session['user_id'], receiver_id)
        return jsonify(messages)

if __name__ == '__main__':
    app.run(debug=True)
