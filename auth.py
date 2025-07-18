from flask import Blueprint, redirect, url_for, session, flash, request, render_template
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import json

load_dotenv()

# Simple user storage (in production, use a proper database)
USERS_FILE = 'users.json'

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# User class for session management
class User:
    def __init__(self, user_id, email, name, login_method='oauth'):
        self.id = user_id
        self.email = email
        self.name = name
        self.login_method = login_method
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def create_manual_user(email, name, password):
        """Create a new manual user with hashed password"""
        users = load_users()
        
        # Check if user already exists
        if email in users:
            return None
        
        # Create new user
        user_data = {
            'email': email,
            'name': name,
            'password_hash': generate_password_hash(password),
            'login_method': 'manual'
        }
        
        users[email] = user_data
        save_users(users)
        return User(email, email, name, 'manual')
    
    @staticmethod
    def authenticate_manual_user(email, password):
        """Authenticate a manual user with email/password"""
        users = load_users()
        
        if email not in users:
            return None
        
        user_data = users[email]
        if check_password_hash(user_data['password_hash'], password):
            return User(email, email, user_data['name'], 'manual')
        
        return None

def login_required_gmail(f):
    """Decorator to require login and @gmail.com email"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return {'error': 'Authentication required'}, 401
        
        if not current_user.email.endswith('@gmail.com'):
            return {'error': 'Only Gmail accounts are allowed'}, 403
        
        return f(*args, **kwargs)
    return decorated_function

def create_auth_blueprint():
    """Create and configure the Google OAuth blueprint with all routes"""
    # Google OAuth configuration
    google_bp = make_google_blueprint(
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scope=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_to='google.google_callback'
    )
    
    # Define the callback route BEFORE registering the blueprint
    @google_bp.route('/google/callback')
    def google_callback():
        """Handle Google OAuth callback"""
        if not google.authorized:
            return {'error': 'Google authorization failed'}, 400
        
        # Get user info from Google
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            user_info = resp.json()
            email = user_info.get('email')
            name = user_info.get('name', 'Unknown')
            user_id = user_info.get('id')
            
            # Check if email is Gmail
            if not email or not email.endswith('@gmail.com'):
                return {'error': 'Only Gmail accounts are allowed'}, 403
            
            # Create user object and log in
            user = User(user_id, email, name)
            login_user(user)
            
            # Store user info in session
            session['user_email'] = email
            session['user_name'] = name
            
            return redirect(url_for('welcome'))
        else:
            return {'error': 'Failed to get user info from Google'}, 400
    
    return google_bp

def init_auth(app):
    """Initialize authentication with the Flask app"""
    # Create the blueprint with all routes defined
    google_bp = create_auth_blueprint()
    
    # Register the blueprint
    app.register_blueprint(google_bp, url_prefix='/auth')
    
    # Define app-level routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login route - handles both OAuth redirect and manual login"""
        if request.method == 'GET':
            # Show login form
            return render_template('login.html')
        
        # Handle manual login
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password')
            return render_template('login.html')
        
        # Authenticate user
        user = User.authenticate_manual_user(email, password)
        if user:
            login_user(user)
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['login_method'] = 'manual'
            return redirect(url_for('welcome'))
        else:
            flash('Invalid email or password')
            return render_template('login.html')
    
    @app.route('/oauth-login')
    def oauth_login():
        """Initiate Google OAuth login"""
        if not google.authorized:
            return redirect(url_for('google.login'))
        return redirect(url_for('welcome'))
    
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        """Signup route for manual registration"""
        if request.method == 'GET':
            return render_template('signup.html')
        
        # Handle signup form
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if not email or not name or not password:
            flash('Please fill in all fields')
            return render_template('signup.html')
        
        # Create user
        user = User.create_manual_user(email, name, password)
        if user:
            login_user(user)
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['login_method'] = 'manual'
            flash('Account created successfully!')
            return redirect(url_for('welcome'))
        else:
            flash('User with this email already exists')
            return render_template('signup.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Log out the current user"""
        logout_user()
        session.clear()
        return redirect(url_for('login')) 