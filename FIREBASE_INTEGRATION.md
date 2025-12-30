# Firebase Authentication Integration

## Overview

This document describes the integration of Firebase Authentication from the demo files (`demo_login.html` and `demo_home.html`) into the production Django application.

## Integration Summary

### 1. Login Page (`templates/login.html`)

**Features Integrated:**
- Full Firebase Authentication UI with Google Sign-In
- Email/password authentication
- Loading states and error handling
- Success messages with auto-redirect
- Connection status indicators
- Professional styling with Tailwind CSS

**Key Changes:**
- Replaced the basic login template with the enhanced demo UI
- Integrated Firebase SDK (v10.7.1) directly in the template
- Added backend integration via `/accounts/verify-token/` endpoint
- Implemented proper error handling and user feedback
- Added CSRF token handling for secure backend communication

### 2. Base Template (`templates/base.html`)

**Features Integrated:**
- User dropdown menu with profile information
- Logout functionality with Firebase sign-out
- Firebase authentication state monitoring
- Session management

**Key Changes:**
- Added user dropdown with profile display (name and email)
- Integrated Firebase SDK for authentication state checking
- Added logout functionality that clears both Firebase and Django sessions
- Improved navigation with active user indicators

### 3. Backend (`accounts/views.py`)

**Endpoints:**

#### `verify_token` (POST `/accounts/verify-token/`)
- Verifies Firebase ID tokens
- Creates or updates Django user accounts automatically
- Maps Firebase UID to Django User model
- Stores Firebase token in session
- Returns user information on success

**Key Features:**
- Automatic user creation on first sign-in
- Firebase UID to Django User mapping via `firebase_uid` field
- Session management with 1-hour expiry
- Comprehensive error handling and logging

#### `logout_view` (POST/GET `/accounts/logout/`)
- Clears Django session
- Removes Firebase token cookie
- Redirects to login page

## Authentication Flow

### Sign-In Flow:
1. User enters credentials or clicks Google Sign-In on `/accounts/login/`
2. Firebase Authentication validates credentials
3. Frontend receives Firebase ID token
4. Token sent to `/accounts/verify-token/` endpoint
5. Backend verifies token with Firebase Admin SDK
6. Django creates/updates user account and session
7. User redirected to home page (`/`)

### Session Management:
- Firebase tokens stored in cookies (1-hour expiry)
- Django session stores user_id and firebase_token
- Session expiry: 1 hour (matches Firebase token expiry)

### Sign-Out Flow:
1. User clicks "Sign Out" in dropdown menu
2. Firebase sign-out called in frontend
3. Backend `/accounts/logout/` endpoint clears session
4. Firebase token cookie removed
5. User redirected to login page

## Firebase Configuration

### Frontend Configuration (in templates):
```javascript
const firebaseConfig = {
    apiKey: "AIzaSyAelVAxdAl9C_UxRqc2lWZNABDRNt1kPNo",
    authDomain: "fractionball-lms.firebaseapp.com",
    projectId: "fractionball-lms",
    storageBucket: "fractionball-lms.firebasestorage.app",
    messagingSenderId: "110595744029",
    appId: "1:110595744029:web:c66d6c0cdc0df3cf33c1f4",
    measurementId: "G-LXELEY5CP8"
};
```

### Backend Configuration (in settings.py):
- Firebase Admin SDK configured via environment variables
- Service account credentials in `FIREBASE_CONFIG` setting

## Security Considerations

1. **CSRF Protection**: All backend endpoints use CSRF tokens
2. **Token Verification**: Firebase ID tokens verified server-side
3. **Session Security**: Secure session cookies with HTTPOnly flag
4. **Token Expiry**: 1-hour token and session expiry
5. **HTTPS**: Recommended for production (configured via settings)

## Files Modified

### Templates:
- `templates/login.html` - Complete Firebase auth UI
- `templates/base.html` - User dropdown and logout
- `templates/home.html` - Minor style updates

### Backend:
- `accounts/views.py` - Token verification and logout
- `accounts/urls.py` - URL patterns (unchanged)

### Documentation:
- `FIREBASE_INTEGRATION.md` - This document

## Demo Files Status

The following demo files have been integrated and are no longer needed:
- `demo_login.html` - Integrated into `templates/login.html`
- `demo_home.html` - UI integrated into `templates/home.html` and `templates/base.html`

**Note:** Demo files can be safely deleted or moved to an archive folder.

## Testing Checklist

- [ ] Login with Google Sign-In works
- [ ] Login with email/password works
- [ ] Error messages display correctly
- [ ] User dropdown shows correct information
- [ ] Logout clears session and redirects to login
- [ ] Protected pages redirect to login when not authenticated
- [ ] Session expires after 1 hour
- [ ] Multiple users can sign in on different devices
- [ ] Firebase token verification works correctly

## Environment Variables Required

For production deployment, ensure these are set:

```bash
# Firebase Admin SDK
FIREBASE_PROJECT_ID=fractionball-lms
FIREBASE_PRIVATE_KEY_ID=<from service account>
FIREBASE_PRIVATE_KEY=<from service account>
FIREBASE_CLIENT_EMAIL=<from service account>
FIREBASE_CLIENT_ID=<from service account>
FIREBASE_CLIENT_X509_CERT_URL=<from service account>

# Django
SECRET_KEY=<your secret key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Security
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
```

## Future Enhancements

1. **Password Reset**: Add "Forgot Password" flow using Firebase
2. **Email Verification**: Require email verification on sign-up
3. **Multi-Factor Auth**: Add 2FA support
4. **Social Providers**: Add Microsoft, Apple sign-in
5. **Profile Management**: Allow users to update profile information
6. **Session Analytics**: Track user sessions and activity

## Support

For issues or questions:
- Check Firebase Console for authentication logs
- Review Django logs in `logs/django.log`
- Verify Firebase service account credentials
- Check browser console for frontend errors

## References

- [Firebase Authentication Docs](https://firebase.google.com/docs/auth)
- [Django Session Framework](https://docs.djangoproject.com/en/stable/topics/http/sessions/)
- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)







































