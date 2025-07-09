from flask import Blueprint, jsonify, request
from auth import login_required_gmail
import logging
from datetime import datetime
from database import UserStats, Customer
from sheets_sync import sync_google_sheets, get_sheets_connection_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

@api_bp.route('/dashboard')
@login_required_gmail
def dashboard():
    """Protected dashboard route - returns user info and real stats"""
    from flask_login import current_user
    
    # Get real user statistics
    stats = UserStats.get_user_stats(current_user.email)
    sheets_status = get_sheets_connection_status(current_user.email)
    
    return jsonify({
        'user': {
            'name': current_user.name,
            'email': current_user.email,
            'id': current_user.id
        },
        'stats': stats,
        'sheets': sheets_status,
        'features': {
            'sms_campaigns': 'Active',
            'review_automation': 'Active',
            'analytics': 'Coming soon',
            'customer_retention': 'Coming soon'
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

@api_bp.route('/sync-sheets', methods=['POST'])
@login_required_gmail
def sync_sheets():
    """Trigger Google Sheets sync"""
    from flask_login import current_user
    
    try:
        result = sync_google_sheets(current_user.email)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Sheets sync error for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Sync failed: {str(e)}'
        }), 500

@api_bp.route('/upload-csv', methods=['POST'])
@login_required_gmail
def upload_csv():
    """Upload CSV file and add customers"""
    from flask_login import current_user
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename or not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        
        # Create customers from CSV
        customers = Customer.create_from_csv(current_user.email, csv_content)
        
        if not customers:
            return jsonify({'error': 'No valid customers found in CSV'}), 400
        
        # Save customers (this will handle duplicates in the existing logic)
        Customer.save_customers(customers)
        
        logger.info(f"📊 CSV Upload completed:")
        logger.info(f"   User: {current_user.email}")
        logger.info(f"   Customers added: {len(customers)}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully added {len(customers)} customers from CSV',
            'customers_added': len(customers)
        })
        
    except Exception as e:
        logger.error(f"CSV upload error for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@api_bp.route('/send-campaign', methods=['POST'])
@login_required_gmail
def send_campaign():
    """Send SMS campaign to customers (simulated)"""
    from flask_login import current_user
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    message_template = data.get('message', 'Thank you for your business! Please leave us a review.')
    customer_ids = data.get('customer_ids', [])
    
    try:
        customers = Customer.get_customers_by_user(current_user.email)
        
        # If no specific customers, send to all
        if not customer_ids:
            target_customers = customers
        else:
            target_customers = [c for c in customers if c.id in customer_ids]
        
        sent_count = 0
        for customer in target_customers:
            # Simulate sending SMS
            personalized_message = message_template.replace('{name}', customer.name)
            
            logger.info(f"📱 MOCK SMS CAMPAIGN:")
            logger.info(f"   To: {customer.name} ({customer.phone})")
            logger.info(f"   Message: {personalized_message}")
            logger.info(f"   User: {current_user.email}")
            
            # Update customer SMS status
            Customer.update_customer_sms_status(customer.id, 'sent')
            sent_count += 1
        
        logger.info(f"📊 Campaign completed: {sent_count} messages sent")
        
        return jsonify({
            'success': True,
            'message': f'Campaign sent to {sent_count} customers',
            'sent_count': sent_count
        })
        
    except Exception as e:
        logger.error(f"Campaign send error for {current_user.email}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Campaign failed: {str(e)}'
        }), 500

def init_routes(app):
    """Initialize API routes with the Flask app"""
    app.register_blueprint(api_bp, url_prefix='/api') 