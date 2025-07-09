"""
Google Sheets sync functionality for Krypton SMS
This simulates Google Sheets integration without requiring actual API setup
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from database import Customer
import logging

logger = logging.getLogger(__name__)

# Mock Google Sheets data file
SHEETS_DATA_FILE = 'mock_sheets_data.json'

def load_mock_sheets_data() -> List[Dict]:
    """Load mock Google Sheets data from file"""
    if os.path.exists(SHEETS_DATA_FILE):
        with open(SHEETS_DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_mock_sheets_data(data: List[Dict]):
    """Save mock Google Sheets data to file"""
    with open(SHEETS_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def create_sample_sheets_data():
    """Create sample Google Sheets data for testing"""
    sample_data = [
        {"name": "John Smith", "phone": "555-0101", "email": "john@example.com"},
        {"name": "Sarah Johnson", "phone": "555-0102", "email": "sarah@example.com"},
        {"name": "Mike Wilson", "phone": "555-0103", "email": "mike@example.com"},
        {"name": "Lisa Brown", "phone": "555-0104", "email": "lisa@example.com"},
        {"name": "David Garcia", "phone": "555-0105", "email": "david@example.com"},
    ]
    save_mock_sheets_data(sample_data)
    return sample_data

def sync_google_sheets(user_email: str) -> Dict:
    """
    Simulate syncing from Google Sheets
    In production, this would connect to Google Sheets API
    """
    try:
        # Load mock data (in production, this would fetch from Google Sheets API)
        sheets_data = load_mock_sheets_data()
        
        # If no mock data exists, create some
        if not sheets_data:
            sheets_data = create_sample_sheets_data()
            logger.info("📊 Created sample Google Sheets data for testing")
        
        # Sync customers from sheets data
        result = Customer.sync_from_google_sheets(user_email, sheets_data)
        
        # Log the sync operation
        logger.info(f"📈 GOOGLE SHEETS SYNC COMPLETED:")
        logger.info(f"   User: {user_email}")
        logger.info(f"   Added: {result['added']} new customers")
        logger.info(f"   Skipped: {result['skipped']} duplicates")
        logger.info(f"   Total Processed: {result['total_processed']}")
        logger.info(f"   Timestamp: {datetime.now().isoformat()}")
        
        return {
            'success': True,
            'message': f"Synced {result['added']} new customers from Google Sheets",
            'details': result,
            'last_sync': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Google Sheets sync failed for {user_email}: {str(e)}")
        return {
            'success': False,
            'message': f"Sync failed: {str(e)}",
            'details': None,
            'last_sync': None
        }

def add_mock_customer_to_sheets(name: str, phone: str, email: str = None):
    """Add a customer to mock sheets data (simulates adding to Google Sheets)"""
    sheets_data = load_mock_sheets_data()
    new_customer = {"name": name, "phone": phone, "email": email or ""}
    sheets_data.append(new_customer)
    save_mock_sheets_data(sheets_data)
    logger.info(f"📝 Added customer to mock Google Sheets: {name} ({phone})")

def get_sheets_connection_status(user_email: str) -> Dict:
    """Check if user has Google Sheets connected"""
    customers = Customer.get_customers_by_user(user_email)
    sheets_customers = [c for c in customers if c.source == 'sheets']
    
    if sheets_customers:
        last_sync = max(c.last_synced_at for c in sheets_customers if c.last_synced_at)
        return {
            'connected': True,
            'last_sync': last_sync.isoformat() if last_sync else None,
            'customers_from_sheets': len(sheets_customers)
        }
    else:
        return {
            'connected': False,
            'last_sync': None,
            'customers_from_sheets': 0
        }

def schedule_background_sync(user_email: str):
    """
    Simulate scheduling a background sync job
    In production, this would use Celery, RQ, or similar task queue
    """
    logger.info(f"📅 Scheduled background sync for {user_email}")
    # For now, just run the sync immediately
    return sync_google_sheets(user_email)