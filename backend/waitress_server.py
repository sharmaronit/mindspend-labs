"""
Production-grade Flask server using Waitress (works well on Windows)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import bcrypt
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
SECRET_KEY = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
DATABASE = 'mindspend.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for better concurrency
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            username TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
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
            category TEXT,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User financial metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_financial_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            monthly_income REAL,
            rent_mortgage REAL,
            utilities REAL,
            groceries REAL,
            transportation REAL,
            healthcare REAL,
            entertainment REAL,
            other_expenses REAL,
            savings_goal REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_token(user_id, email):
    """Create a JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user_id = payload['user_id']
        request.user_email = payload['email']
        return f(*args, **kwargs)
    
    return decorated_function

# Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'name': 'MindSpend API',
        'version': '1.0.0',
        'status': 'running'
    })

@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (email, password_hash, username) VALUES (?, ?, ?)',
            (email, password_hash, username)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        # Create token
        token = create_token(user_id, email)
        
        return jsonify({
            'access_token': token,
            'refresh_token': token,
            'token_type': 'bearer',
            'user_id': user_id,
            'email': email,
            'username': username
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, password_hash, username FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        token = create_token(user['id'], user['email'])
        
        return jsonify({
            'access_token': token,
            'refresh_token': token,
            'token_type': 'bearer',
            'user_id': user['id'],
            'email': user['email'],
            'username': user['username']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/refresh', methods=['POST'])
@require_auth
def refresh():
    """Refresh authentication token"""
    token = create_token(request.user_id, request.user_email)
    return jsonify({
        'access_token': token,
        'refresh_token': token,
        'token_type': 'bearer'
    })

@app.route('/user/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, username FROM users WHERE id = ?', (request.user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'username': user['username']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE users SET username = ? WHERE id = ?',
            (username, request.user_id)
        )
        conn.commit()
        
        cursor.execute('SELECT id, email, username FROM users WHERE id = ?', (request.user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'username': user['username']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current password hash
        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (request.user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not verify_password(current_password, user['password_hash']):
            conn.close()
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        new_password_hash = hash_password(new_password)
        cursor.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (new_password_hash, request.user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Password updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user/metrics', methods=['GET'])
@require_auth
def get_metrics():
    """Get user financial metrics"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_financial_metrics WHERE user_id = ?', (request.user_id,))
        metrics = cursor.fetchone()
        conn.close()
        
        if not metrics:
            return jsonify({'message': 'No metrics found'}), 404
        
        return jsonify(dict(metrics))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user/metrics', methods=['POST'])
@require_auth
def update_metrics():
    """Update user financial metrics"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if metrics exist
        cursor.execute('SELECT id FROM user_financial_metrics WHERE user_id = ?', (request.user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE user_financial_metrics 
                SET monthly_income = ?, rent_mortgage = ?, utilities = ?, groceries = ?,
                    transportation = ?, healthcare = ?, entertainment = ?, other_expenses = ?,
                    savings_goal = ?
                WHERE user_id = ?
            ''', (
                data.get('monthly_income'), data.get('rent_mortgage'), data.get('utilities'),
                data.get('groceries'), data.get('transportation'), data.get('healthcare'),
                data.get('entertainment'), data.get('other_expenses'), data.get('savings_goal'),
                request.user_id
            ))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO user_financial_metrics 
                (user_id, monthly_income, rent_mortgage, utilities, groceries, transportation,
                 healthcare, entertainment, other_expenses, savings_goal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.user_id, data.get('monthly_income'), data.get('rent_mortgage'),
                data.get('utilities'), data.get('groceries'), data.get('transportation'),
                data.get('healthcare'), data.get('entertainment'), data.get('other_expenses'),
                data.get('savings_goal')
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Metrics updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MindSpend API Server Starting...")
    print("=" * 60)
    print("\n📊 Initializing database...")
    
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        exit(1)
    
    print("\n🌐 Starting Waitress WSGI server...")
    print("📍 Server will be available at: http://127.0.0.1:8001")
    print("🔧 Using Waitress (production-grade server for Windows)")
    print("\n⚡ Server is ready to accept connections!")
    print("=" * 60)
    print("\n💡 Press CTRL+C to stop the server\n")
    
    from waitress import serve
    serve(app, host='127.0.0.1', port=8001, threads=4)
