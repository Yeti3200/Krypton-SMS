from flask import Flask, jsonify, render_template
from flask_login import LoginManager
from auth import init_auth, User
from routes import init_routes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user from session"""
        # In a real app, you'd load from database
        # For now, we'll return None and let the session handle it
        return None
    
    # Initialize authentication
    init_auth(app)
    
    # Initialize routes
    init_routes(app)
    
    # Landing page route
    @app.route('/')
    def landing():
        """Serve the landing page"""
        return render_template('landing.html')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'app': 'Krypton Outreach API',
            'version': '1.0.0'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

# Create the app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    # Check for required environment variables
    required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with these variables.")
        exit(1)
    
    print("🚀 Starting Krypton Outreach API...")
    print("📱 Available endpoints:")
    print("   - GET  /                    # Landing page")
    print("   - GET  /health")
    print("   - GET  /login")
    print("   - GET  /logout")
    print("   - GET  /api/dashboard")
    print("   - POST /api/send-test-sms")
    print("\n🔐 Google OAuth configured")
    print("📧 Gmail-only authentication enabled")
    
    # Use Render's PORT environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=False, host='0.0.0.0', port=port)