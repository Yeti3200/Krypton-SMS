from flask import Blueprint, jsonify, request
from auth import login_required_gmail
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

@api_bp.route('/dashboard')
@login_required_gmail
def dashboard():
    """Protected dashboard route - returns user info and placeholder for future features"""
    from flask_login import current_user
    
    return jsonify({
        'user': {
            'name': current_user.name,
            'email': current_user.email,
            'id': current_user.id
        },
        'features': {
            'sms_campaigns': 'Coming soon',
            'review_automation': 'Coming soon',
            'analytics': 'Coming soon',
            'customer_retention': 'Coming soon'
        },
        'stats': {
            'total_campaigns': 0,
            'total_reviews': 0,
            'total_customers': 0
        }
    })

@api_bp.route('/send-test-sms', methods=['POST'])
@login_required_gmail
def send_test_sms():
    """Mock SMS endpoint - logs to console"""
    from flask_login import current_user
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    phone_number = data.get('phone_number')
    message = data.get('message', 'Test SMS from Krypton')
    
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400
    
    # Mock SMS sending - log to console
    logger.info(f"📱 MOCK SMS SENT:")
    logger.info(f"   To: {phone_number}")
    logger.info(f"   Message: {message}")
    logger.info(f"   User: {current_user.email}")
    logger.info(f"   Timestamp: {datetime.now().isoformat()}")
    
    return jsonify({
        'success': True,
        'message': 'Test SMS logged successfully',
        'details': {
            'phone_number': phone_number,
            'message': message,
            'status': 'sent'
        }
    })

def init_routes(app):
    """Initialize API routes with the Flask app"""
    app.register_blueprint(api_bp, url_prefix='/api') 