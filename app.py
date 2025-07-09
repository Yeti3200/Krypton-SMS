from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from flask_login import LoginManager, login_required, current_user
from auth import init_auth, User
from routes import init_routes
from onboarding import init_onboarding
from database import UserStats, Customer
import logging
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
    login_manager.login_view = 'login'  # Redirect to login if not authenticated
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user from session"""
        # Reconstruct user from session data
        if 'user_email' in session and 'user_name' in session:
            return User(user_id, session['user_email'], session['user_name'])
        return None
    
    # Initialize authentication
    init_auth(app)
    
    # Initialize routes
    init_routes(app)
    
    # Initialize onboarding
    init_onboarding(app)
    
    # Landing page route
    @app.route('/')
    def landing():
        """Serve the landing page"""
        return render_template('landing.html')
    
    # Welcome route (replaces onboarding for first-time users)
    @app.route('/welcome')
    @login_required
    def welcome():
        """Welcome screen for first-time users"""
        # If user has already seen welcome (has customers), redirect to dashboard
        if UserStats.user_has_seen_welcome(current_user.email):
            return redirect(url_for('dashboard'))
        
        return render_template('welcome.html', user=current_user)
    
    # Send test message route
    @app.route('/send-test', methods=['POST'])
    @login_required
    def send_test():
        """Handle test message sending from welcome screen"""
        try:
            customer_name = request.form.get('customerName', '').strip()
            customer_phone = request.form.get('customerPhone', '').strip()
            
            if not customer_name or not customer_phone:
                return jsonify({
                    'success': False,
                    'message': 'Please provide both name and phone number'
                }), 400
            
            # Add test customer
            success = Customer.add_customer_if_new(
                current_user.email, 
                customer_name, 
                customer_phone, 
                'welcome'
            )
            
            if not success:
                # Customer already exists, but that's ok for test
                customers = Customer.get_customers_by_user(current_user.email)
                existing_customer = next((c for c in customers if c.phone == customer_phone), None)
                if existing_customer:
                    customer_name = existing_customer.name
            
            # Simulate sending test SMS
            test_message = f"Hi {customer_name}, thanks for trying Krypton SMS! This is a test message to show how review requests work. 🚀"
            
            # Log the test SMS
            logging.info(f"📱 WELCOME TEST SMS:")
            logging.info(f"   To: {customer_name} ({customer_phone})")
            logging.info(f"   Message: {test_message}")
            logging.info(f"   User: {current_user.email}")
            logging.info(f"   Type: Welcome Test")
            
            return jsonify({
                'success': True,
                'message': f'Test message sent to {customer_name}!',
                'details': {
                    'customer_name': customer_name,
                    'customer_phone': customer_phone,
                    'message': test_message
                }
            })
            
        except Exception as e:
            logging.error(f"Welcome test error for {current_user.email}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to send test message. Please try again.'
            }), 500
    
    # Dashboard route
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Protected dashboard route - shows welcome or dashboard"""
        user_stats = UserStats.get_user_stats(current_user.email)
        
        # If user hasn't seen welcome yet, redirect to welcome
        if not UserStats.user_has_seen_welcome(current_user.email):
            return redirect(url_for('welcome'))
        
        return render_template('dashboard.html', 
                             user=current_user,
                             stats=user_stats)
    
    # Onboarding wizard route
    @app.route('/onboarding')
    @login_required
    def onboarding():
        """3-step onboarding wizard"""
        return render_template('onboarding.html', user=current_user)
    
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