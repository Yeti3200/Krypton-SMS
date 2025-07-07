"""
Onboarding routes and logic for Krypton SMS
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import Customer, Campaign, UserStats
import os
import csv
from datetime import datetime
import requests
from typing import List

# Create onboarding blueprint
onboarding_bp = Blueprint('onboarding', __name__)

# Default SMS message template
DEFAULT_SMS_MESSAGE = """Hi {name}! 

Thanks for choosing us! We'd love to hear about your experience.

Could you please leave us a quick review? It really helps our small business grow.

👉 Leave a review here: [YOUR_REVIEW_LINK]

Thanks again!
- The Team"""

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure upload folder exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@onboarding_bp.route('/upload-customers', methods=['POST'])
@login_required
def upload_customers():
    """Step 1: Upload customer CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    try:
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        
        # Parse and create customers
        customers = Customer.create_from_csv(current_user.email, csv_content)
        
        if not customers:
            return jsonify({'error': 'No valid customers found in CSV. Please check your file format.'}), 400
        
        # Save customers to database
        Customer.save_customers(customers)
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(customers)} customers',
            'customers': [{'name': c.name, 'phone': c.phone, 'email': c.email} for c in customers]
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@onboarding_bp.route('/add-manual-customers', methods=['POST'])
@login_required
def add_manual_customers():
    """Step 1: Add customers manually (alternative to CSV upload)"""
    try:
        data = request.get_json()
        customer_data = data.get('customers', [])
        
        if not customer_data:
            return jsonify({'error': 'No customers provided'}), 400
        
        # Validate customer data
        customers = []
        for i, customer_info in enumerate(customer_data):
            name = customer_info.get('name', '').strip()
            phone = customer_info.get('phone', '').strip()
            email = customer_info.get('email', '').strip()
            
            if not name or not phone:
                return jsonify({'error': f'Customer {i+1}: Name and phone are required'}), 400
            
            # Generate unique ID
            customer_id = f"{current_user.email}_manual_{i}_{datetime.now().timestamp()}"
            customer = Customer(customer_id, current_user.email, name, phone, email if email else None)
            customers.append(customer)
        
        if len(customers) > 5:
            return jsonify({'error': 'Maximum 5 customers allowed for manual entry'}), 400
        
        # Save customers to database
        Customer.save_customers(customers)
        
        return jsonify({
            'success': True,
            'message': f'Successfully added {len(customers)} customer{"s" if len(customers) != 1 else ""}',
            'customers': [{'name': c.name, 'phone': c.phone, 'email': c.email} for c in customers]
        })
        
    except Exception as e:
        return jsonify({'error': f'Error saving customers: {str(e)}'}), 500

@onboarding_bp.route('/customize-message', methods=['POST'])
@login_required
def customize_message():
    """Step 2: Customize SMS message"""
    message = request.json.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Store message in session for step 3
    from flask import session
    session['sms_message'] = message
    
    return jsonify({
        'success': True,
        'message': 'Message saved successfully',
        'preview': message
    })

@onboarding_bp.route('/launch-campaign', methods=['POST'])
@login_required
def launch_campaign():
    """Step 3: Launch SMS campaign"""
    from flask import session
    
    # Get message from session
    message = session.get('sms_message', DEFAULT_SMS_MESSAGE)
    campaign_name = request.json.get('campaign_name', f"Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Get user's customers
    customers = Customer.get_customers_by_user(current_user.email)
    
    if not customers:
        return jsonify({'error': 'No customers found. Please upload customers first.'}), 400
    
    # Create campaign
    campaign_id = f"campaign_{current_user.email}_{datetime.now().timestamp()}"
    campaign = Campaign(campaign_id, current_user.email, campaign_name, message)
    campaign.total_customers = len(customers)
    campaign.status = 'sending'
    campaign.save()
    
    # Send SMS to each customer
    results = []
    for customer in customers:
        try:
            # Personalize message
            personalized_message = message.replace('{name}', customer.name)
            
            # Send SMS (using your existing SMS logic)
            sms_result = send_sms_message(customer.phone, personalized_message)
            
            if sms_result['success']:
                Customer.update_customer_sms_status(customer.id, 'sent')
                campaign.sent_count += 1
                results.append({
                    'customer_id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone,
                    'status': 'sent',
                    'message': 'SMS sent successfully'
                })
            else:
                Customer.update_customer_sms_status(customer.id, 'failed')
                campaign.failed_count += 1
                results.append({
                    'customer_id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone,
                    'status': 'failed',
                    'message': sms_result.get('error', 'Unknown error')
                })
                
        except Exception as e:
            campaign.failed_count += 1
            results.append({
                'customer_id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'status': 'failed',
                'message': str(e)
            })
    
    # Update campaign with results
    campaign.customer_results = results
    campaign.status = 'completed'
    campaign.save()
    
    # Clear session message
    session.pop('sms_message', None)
    
    return jsonify({
        'success': True,
        'campaign_id': campaign_id,
        'results': results,
        'summary': {
            'total': len(customers),
            'sent': campaign.sent_count,
            'failed': campaign.failed_count
        }
    })

def send_sms_message(phone: str, message: str) -> dict:
    """
    Send SMS message via Telnyx API
    Replace with your actual SMS service integration
    """
    # Mock SMS sending for now - replace with actual Telnyx API call
    try:
        # Example Telnyx API integration:
        # telnyx_api_key = os.getenv('TELNYX_API_KEY')
        # telnyx_phone_number = os.getenv('TELNYX_PHONE_NUMBER')
        # 
        # response = requests.post(
        #     'https://api.telnyx.com/v2/messages',
        #     headers={
        #         'Authorization': f'Bearer {telnyx_api_key}',
        #         'Content-Type': 'application/json'
        #     },
        #     json={
        #         'from': telnyx_phone_number,
        #         'to': phone,
        #         'text': message
        #     }
        # )
        # 
        # if response.status_code == 200:
        #     return {'success': True, 'message_id': response.json()['data']['id']}
        # else:
        #     return {'success': False, 'error': f'API error: {response.status_code}'}
        
        # Mock success for testing
        print(f"📱 MOCK SMS SENT:")
        print(f"   To: {phone}")
        print(f"   Message: {message}")
        print(f"   User: {current_user.email}")
        
        return {'success': True, 'message_id': f'mock_{datetime.now().timestamp()}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@onboarding_bp.route('/get-default-message')
@login_required
def get_default_message():
    """Get default SMS message template"""
    return jsonify({
        'message': DEFAULT_SMS_MESSAGE,
        'placeholders': ['{name}']
    })

@onboarding_bp.route('/campaign-results/<campaign_id>')
@login_required
def campaign_results(campaign_id):
    """View campaign results"""
    campaign = Campaign.get_campaign_by_id(campaign_id)
    
    if not campaign or campaign.user_email != current_user.email:
        flash('Campaign not found')
        return redirect(url_for('dashboard'))
    
    return render_template('campaign_results.html', 
                         campaign=campaign, 
                         user=current_user)

def init_onboarding(app):
    """Initialize onboarding routes"""
    app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
    ensure_upload_folder()