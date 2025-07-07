from flask import Blueprint, redirect, url_for, session, flash, request
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

# Simple user class for session management
class User:
    def __init__(self, user_id, email, name):
        self.id = user_id
        self.email = email
        self.name = name
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

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
            
            return redirect(url_for('api.dashboard'))
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
    @app.route('/login')
    def login():
        """Initiate Google OAuth login"""
        if not google.authorized:
            return redirect(url_for('google.login'))
        return redirect(url_for('api.dashboard'))
    
    @app.route('/logout')
    @login_required
    def logout():
        """Log out the current user"""
        logout_user()
        session.clear()
        return {'message': 'Logged out successfully'} 