"""
Database models and setup for Krypton SMS
In production, replace with proper database like PostgreSQL
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import csv
from io import StringIO

# Database files
CUSTOMERS_FILE = 'customers.json'
CAMPAIGNS_FILE = 'campaigns.json'

def load_json_db(filename: str) -> Dict:
    """Load data from JSON file"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_json_db(filename: str, data: Dict):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)

class Customer:
    """Customer model"""
    
    def __init__(self, customer_id: str, user_email: str, name: str, phone: str, email: str = None):
        self.id = customer_id
        self.user_email = user_email
        self.name = name
        self.phone = phone
        self.email = email
        self.created_at = datetime.now()
        self.sms_sent = False
        self.sms_status = None
        self.review_received = False
    
    def to_dict(self) -> Dict:
        """Convert customer to dictionary"""
        return {
            'id': self.id,
            'user_email': self.user_email,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'sms_sent': self.sms_sent,
            'sms_status': self.sms_status,
            'review_received': self.review_received
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create customer from dictionary"""
        customer = cls(
            data['id'],
            data['user_email'],
            data['name'],
            data['phone'],
            data.get('email')
        )
        customer.created_at = datetime.fromisoformat(data['created_at'])
        customer.sms_sent = data.get('sms_sent', False)
        customer.sms_status = data.get('sms_status')
        customer.review_received = data.get('review_received', False)
        return customer
    
    @staticmethod
    def create_from_csv(user_email: str, csv_content: str) -> List['Customer']:
        """Create customers from CSV content"""
        customers = []
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        for i, row in enumerate(csv_reader):
            # Generate unique ID
            customer_id = f"{user_email}_{i}_{datetime.now().timestamp()}"
            
            # Extract data (flexible column names)
            name = row.get('Name') or row.get('name') or row.get('NAME') or ''
            phone = row.get('Phone') or row.get('phone') or row.get('PHONE') or ''
            email = row.get('Email') or row.get('email') or row.get('EMAIL') or ''
            
            if name and phone:
                customer = Customer(customer_id, user_email, name, phone, email)
                customers.append(customer)
        
        return customers
    
    @staticmethod
    def save_customers(customers: List['Customer']):
        """Save customers to database"""
        db = load_json_db(CUSTOMERS_FILE)
        
        for customer in customers:
            db[customer.id] = customer.to_dict()
        
        save_json_db(CUSTOMERS_FILE, db)
    
    @staticmethod
    def get_customers_by_user(user_email: str) -> List['Customer']:
        """Get all customers for a user"""
        db = load_json_db(CUSTOMERS_FILE)
        customers = []
        
        for customer_data in db.values():
            if customer_data['user_email'] == user_email:
                customers.append(Customer.from_dict(customer_data))
        
        return customers
    
    @staticmethod
    def update_customer_sms_status(customer_id: str, status: str):
        """Update SMS status for a customer"""
        db = load_json_db(CUSTOMERS_FILE)
        if customer_id in db:
            db[customer_id]['sms_sent'] = True
            db[customer_id]['sms_status'] = status
            save_json_db(CUSTOMERS_FILE, db)

class Campaign:
    """Campaign model"""
    
    def __init__(self, campaign_id: str, user_email: str, name: str, message: str):
        self.id = campaign_id
        self.user_email = user_email
        self.name = name
        self.message = message
        self.created_at = datetime.now()
        self.status = 'created'  # created, sending, completed, failed
        self.total_customers = 0
        self.sent_count = 0
        self.failed_count = 0
        self.customer_results = []  # List of {customer_id, status, error}
    
    def to_dict(self) -> Dict:
        """Convert campaign to dictionary"""
        return {
            'id': self.id,
            'user_email': self.user_email,
            'name': self.name,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'total_customers': self.total_customers,
            'sent_count': self.sent_count,
            'failed_count': self.failed_count,
            'customer_results': self.customer_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create campaign from dictionary"""
        campaign = cls(
            data['id'],
            data['user_email'],
            data['name'],
            data['message']
        )
        campaign.created_at = datetime.fromisoformat(data['created_at'])
        campaign.status = data['status']
        campaign.total_customers = data['total_customers']
        campaign.sent_count = data['sent_count']
        campaign.failed_count = data['failed_count']
        campaign.customer_results = data['customer_results']
        return campaign
    
    def save(self):
        """Save campaign to database"""
        db = load_json_db(CAMPAIGNS_FILE)
        db[self.id] = self.to_dict()
        save_json_db(CAMPAIGNS_FILE, db)
    
    @staticmethod
    def get_campaigns_by_user(user_email: str) -> List['Campaign']:
        """Get all campaigns for a user"""
        db = load_json_db(CAMPAIGNS_FILE)
        campaigns = []
        
        for campaign_data in db.values():
            if campaign_data['user_email'] == user_email:
                campaigns.append(Campaign.from_dict(campaign_data))
        
        return campaigns
    
    @staticmethod
    def get_campaign_by_id(campaign_id: str) -> Optional['Campaign']:
        """Get campaign by ID"""
        db = load_json_db(CAMPAIGNS_FILE)
        if campaign_id in db:
            return Campaign.from_dict(db[campaign_id])
        return None

class UserStats:
    """User statistics helper"""
    
    @staticmethod
    def get_user_stats(user_email: str) -> Dict:
        """Get statistics for a user"""
        customers = Customer.get_customers_by_user(user_email)
        campaigns = Campaign.get_campaigns_by_user(user_email)
        
        total_customers = len(customers)
        total_campaigns = len(campaigns)
        total_reviews = sum(1 for c in customers if c.review_received)
        
        return {
            'total_customers': total_customers,
            'total_campaigns': total_campaigns,
            'total_reviews': total_reviews,
            'customers_with_sms': sum(1 for c in customers if c.sms_sent),
            'active_campaigns': sum(1 for c in campaigns if c.status == 'sending')
        }
    
    @staticmethod
    def user_has_customers(user_email: str) -> bool:
        """Check if user has any customers"""
        customers = Customer.get_customers_by_user(user_email)
        return len(customers) > 0
    
    @staticmethod
    def user_has_campaigns(user_email: str) -> bool:
        """Check if user has any campaigns"""
        campaigns = Campaign.get_campaigns_by_user(user_email)
        return len(campaigns) > 0