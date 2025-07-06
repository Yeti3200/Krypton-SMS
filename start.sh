#!/bin/bash
# Start script for Render deployment

echo "🚀 Starting Krypton Outreach API on Render..."

# Check if environment variables are set
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "❌ Error: Missing required environment variables"
    echo "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Render dashboard"
    exit 1
fi

echo "✅ Environment variables configured"
echo "🔐 Google OAuth ready"
echo "📧 Gmail-only authentication enabled"

# Start the application with gunicorn
exec gunicorn --config gunicorn.conf.py app:create_app 