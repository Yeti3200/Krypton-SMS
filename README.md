# Krypton Outreach API

A Flask backend for the Krypton Outreach app with Google OAuth authentication.

## Features

- 🔐 Google OAuth authentication (Gmail-only)
- 📱 Mock SMS endpoint for testing
- 🛡️ Protected routes with session management
- 📊 Dashboard with user info and placeholder features
- 🚀 Clean, modular code structure

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
5. Copy your Client ID and Client Secret

### 3. Environment Variables

Create a `.env` file based on `env.example`:

```bash
cp env.example .env
```

Edit `.env` with your Google OAuth credentials:

```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=your-super-secret-key-change-this-in-production
```

### 4. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### Authentication
- `GET /login` - Initiate Google OAuth login
- `GET /logout` - Log out current user

### Protected Routes (Requires Gmail login)
- `GET /api/dashboard` - Get user info and feature placeholders
- `POST /api/send-test-sms` - Send mock SMS (logs to console)

### Utility
- `GET /health` - Health check endpoint

## Example Usage

### Login Flow
1. Visit `http://localhost:8000/login`
2. Complete Google OAuth
3. Redirected to dashboard if Gmail account

### Send Test SMS
```bash
curl -X POST http://localhost:8000/api/send-test-sms \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"phone_number": "+1234567890", "message": "Test message"}'
```

## Project Structure

```
├── app.py              # Main Flask application
├── auth.py             # Google OAuth authentication
├── routes.py           # API routes and endpoints
├── requirements.txt    # Python dependencies
├── env.example        # Environment variables template
└── README.md          # This file
```

## Development Notes

- Only Gmail accounts are allowed for authentication
- Session-based authentication (no database required)
- Mock SMS endpoint logs to console for testing
- All responses are JSON (no HTML templates)
- Ready for frontend integration

## Next Steps

- Add database for user persistence
- Implement real SMS sending
- Add more API endpoints for features
- Add rate limiting and security headers
- Deploy to production with proper SSL 