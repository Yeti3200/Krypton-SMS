# Deploying to Render

## Render Configuration

### 1. Environment Variables
Set these in your Render dashboard:

```
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=your-super-secret-key-change-this-in-production
```

### 2. Build Command
```
pip install -r requirements.txt
```

### 3. Start Command
```
./start.sh
```

### 4. Google OAuth Setup for Production

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Add your Render URL to authorized redirect URIs:
   - `https://your-app-name.onrender.com/auth/google/callback`
3. Update your `.env` file with production credentials

### 5. Common Issues & Solutions

#### Issue: App not starting
- Check that all environment variables are set in Render dashboard
- Verify the start command is correct: `./start.sh`

#### Issue: Google OAuth not working
- Make sure your Render URL is added to Google OAuth redirect URIs
- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set correctly

#### Issue: 500 errors
- Check Render logs for specific error messages
- Verify all dependencies are installed correctly

### 6. Testing Your Deployment

1. Visit your Render URL: `https://your-app-name.onrender.com/`
2. Test the health endpoint: `https://your-app-name.onrender.com/health`
3. Test Google OAuth: `https://your-app-name.onrender.com/login`

### 7. Monitoring

- Check Render logs for any errors
- Monitor the `/health` endpoint
- Test all API endpoints after deployment 