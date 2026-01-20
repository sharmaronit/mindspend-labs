"""
Simple Flask Backend - Much simpler than FastAPI!
Run: python flask_server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import jwt
import bcrypt
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
DATABASE = "mindspend.db"

# ============================================
# Database Helper Functions
# ============================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # User transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # User financial metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_financial_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            monthly_income REAL DEFAULT 0,
            rent REAL DEFAULT 0,
            utilities REAL DEFAULT 0,
            tuition REAL DEFAULT 0,
            loans REAL DEFAULT 0,
            insurance REAL DEFAULT 0,
            subscriptions REAL DEFAULT 0,
            other_expenses REAL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database tables created successfully")

# ============================================
# Authentication Helper Functions
# ============================================

def hash_password(password):
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id, email):
    """Create JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        request.user_id = payload['user_id']
        return f(*args, **kwargs)
    return decorated

# ============================================
# Routes
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Flask API is running'})

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Personal Behavioral Analyst API (Flask)',
        'version': '1.0.0',
        'health': '/health'
    })

@app.route('/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Hash password
    password_hash = hash_password(password)
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (email, password_hash, username) VALUES (?, ?, ?)',
                      (email, password_hash, username))
        user_id = cursor.lastrowid
        
        # Create default financial metrics
        cursor.execute('INSERT INTO user_financial_metrics (user_id) VALUES (?)', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Create token
        token = create_token(user_id, email)
        
        return jsonify({
            'access_token': token,
            'refresh_token': token,  # Using same token for simplicity
            'token_type': 'bearer'
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 400

@app.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Create token
    token = create_token(user['id'], email)
    
    return jsonify({
        'access_token': token,
        'refresh_token': token,
        'token_type': 'bearer'
    })

@app.route('/auth/refresh', methods=['POST'])
def refresh():
    """Refresh token"""
    data = request.json
    token = data.get('refresh_token')
    
    payload = verify_token(token)
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Create new token
    new_token = create_token(payload['user_id'], payload['email'])
    
    return jsonify({
        'access_token': new_token,
        'refresh_token': token,
        'token_type': 'bearer'
    })

@app.route('/user/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, username, created_at FROM users WHERE id = ?', 
                  (request.user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return jsonify(dict(user))

@app.route('/user/metrics', methods=['GET'])
@require_auth
def get_metrics():
    """Get user financial metrics"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_financial_metrics WHERE user_id = ?', 
                  (request.user_id,))
    metrics = cursor.fetchone()
    conn.close()
    
    if not metrics:
        return jsonify({'error': 'Metrics not found'}), 404
    
    return jsonify(dict(metrics))

@app.route('/user/metrics', methods=['POST'])
@require_auth
def update_metrics():
    """Update user financial metrics"""
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Update metrics
    cursor.execute('''
        UPDATE user_financial_metrics 
        SET monthly_income = ?, rent = ?, utilities = ?, tuition = ?, 
            loans = ?, insurance = ?, subscriptions = ?, other_expenses = ?
        WHERE user_id = ?
    ''', (
        data.get('monthly_income', 0),
        data.get('rent', 0),
        data.get('utilities', 0),
        data.get('tuition', 0),
        data.get('loans', 0),
        data.get('insurance', 0),
        data.get('subscriptions', 0),
        data.get('other_expenses', 0),
        request.user_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Metrics updated successfully'})

# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    print("📊 Initializing database...")
    init_database()
    print("✅ Server ready!")
    print("📍 Running on http://127.0.0.1:8001")
    print("Press CTRL+C to stop\n")
    
    app.run(host='127.0.0.1', port=8001, debug=False)
