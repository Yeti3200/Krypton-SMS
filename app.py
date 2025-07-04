from flask import Flask, request, jsonify
import requests
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
TELNYX_API_KEY = os.getenv('TELNYX_API_KEY')
FROM_NUMBER = os.getenv('FROM_NUMBER', '+12165416456')
MESSAGING_PROFILE_ID = os.getenv('MESSAGING_PROFILE_ID', '400197d3-0257-4322-90cb-78f7fb42a87c')
TELNYX_API_URL = 'https://api.telnyx.com/v2/messages'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/sms', methods=['POST'])
def handle_sms():
    """Handle incoming SMS webhooks from Telnyx"""
    try:
        # Handle both JSON and form-encoded data from Telnyx
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            webhook_data = request.get_json()
            if not webhook_data or 'data' not in webhook_data:
                logger.warning("Invalid webhook data received")
                return jsonify({'error': 'Invalid webhook data'}), 400
            payload = webhook_data['data']['payload']
            from_number = payload.get('from', {}).get('phone_number')
            message_text = payload.get('text')
        else:
            # Handle form-encoded data
            form_data = request.form
            if not form_data:
                logger.warning("No form data received")
                return jsonify({'error': 'No form data received'}), 400
            
            # Telnyx sends form data with different structure
            from_number = form_data.get('from')
            message_text = form_data.get('text')
            
            # If not directly available, try nested structure
            if not from_number:
                from_number = form_data.get('data[payload][from][phone_number]')
            if not message_text:
                message_text = form_data.get('data[payload][text]')
        
        if not from_number or not message_text:
            logger.warning(f"Missing data - from: {from_number}, text: {message_text}")
            return jsonify({'error': 'Missing phone number or message text'}), 400
        
        # Ignore messages from our own number to prevent loops
        if from_number == FROM_NUMBER:
            logger.info(f"Ignoring message from our own number: {from_number}")
            return jsonify({'status': 'ignored'}), 200
        
        logger.info(f"Incoming SMS from {from_number}: {message_text}")
        
        # Generate reply
        ai_reply = f"Claude says: I got your message: {message_text}"
        
        # Send reply via Telnyx API
        headers = {
            'Authorization': f'Bearer {TELNYX_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        sms_payload = {
            'from': FROM_NUMBER,
            'to': from_number,
            'text': ai_reply,
            'messaging_profile_id': MESSAGING_PROFILE_ID
        }
        
        response = requests.post(TELNYX_API_URL, json=sms_payload, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully sent SMS to {from_number}")
        else:
            logger.error(f"Failed to send SMS. Status: {response.status_code}, Response: {response.text}")
            return jsonify({'error': 'Failed to send SMS'}), 500
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error processing SMS webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Validate required environment variables
    if not TELNYX_API_KEY:
        logger.error("TELNYX_API_KEY not found in environment variables")
        exit(1)
    
    # Development server (production uses gunicorn)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)