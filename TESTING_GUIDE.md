# Firebase Authentication Integration - Testing Guide

## Overview

This guide provides step-by-step instructions to test the integrated Firebase authentication system in the Fraction Ball LMS.

## Prerequisites

1. **Python Environment**: Python 3.8+ with Django installed
2. **Firebase Project**: Firebase project setup (fractionball-lms)
3. **Dependencies**: All requirements from `requirements.txt` installed
4. **Database**: SQLite database initialized (`python manage.py migrate`)

## Quick Start

```bash
# 1. Navigate to project directory
cd /Users/evantran/fractionBallLMS

# 2. Activate virtual environment (if using one)
# source venv/bin/activate

# 3. Run migrations (if not already done)
python manage.py migrate

# 4. Start development server
python manage.py runserver

# 5. Open browser
open http://127.0.0.1:8000/accounts/login/
```

## Test Cases

### 1. Login Page Tests

#### Test 1.1: Firebase Connection
**Steps:**
1. Navigate to `http://127.0.0.1:8000/accounts/login/`
2. Observe the connection status banner

**Expected Result:**
- Blue banner with "Connecting to Firebase..."
- Changes to green "✅ Firebase connected" after ~1 second
- Banner disappears after 2 seconds

**Pass Criteria:** Firebase connection successful

---

#### Test 1.2: Google Sign-In
**Steps:**
1. On login page, click "Continue with Google" button
2. Complete Google authentication in popup
3. Observe behavior after authentication

**Expected Result:**
- Google popup opens
- User authenticates successfully
- Green success message: "Sign in successful! Redirecting..."
- Redirects to home page (`/`) after 1.5 seconds

**Pass Criteria:** Successful Google authentication and redirect

---

#### Test 1.3: Email/Password Sign-In (Existing User)
**Prerequisites:** Create a test user in Firebase Console

**Steps:**
1. Enter email: `test@example.com`
2. Enter password: `password123`
3. Click "Sign In" button

**Expected Result:**
- Button shows loading spinner
- Success message appears
- Redirects to home page

**Pass Criteria:** Successful email/password authentication

---

#### Test 1.4: Email/Password Sign-In (Invalid Credentials)
**Steps:**
1. Enter email: `invalid@example.com`
2. Enter password: `wrongpassword`
3. Click "Sign In" button

**Expected Result:**
- Red error banner appears
- Message: "Invalid email or password"
- User stays on login page

**Pass Criteria:** Appropriate error message displayed

---

#### Test 1.5: Empty Form Submission
**Steps:**
1. Leave email and password fields empty
2. Click "Sign In" button

**Expected Result:**
- Browser validation prevents submission
- "Please fill out this field" message appears

**Pass Criteria:** Form validation works

---

### 2. Home Page Tests

#### Test 2.1: Authenticated User Access
**Prerequisites:** Sign in first

**Steps:**
1. Navigate to `http://127.0.0.1:8000/`
2. Observe navigation bar

**Expected Result:**
- Navigation shows notification bell icon
- User profile icon visible
- User name and email NOT visible (hidden in dropdown)

**Pass Criteria:** Home page loads with authenticated UI

---

#### Test 2.2: User Dropdown
**Steps:**
1. Click on user profile icon (blue circle with person icon)
2. Observe dropdown menu

**Expected Result:**
- Dropdown appears below icon
- Shows user name (first + last or username)
- Shows email address
- Shows "Admin Panel" link (if staff user)
- Shows "Sign Out" button

**Pass Criteria:** Dropdown displays correct user information

---

#### Test 2.3: Dropdown Click Outside
**Steps:**
1. Open user dropdown
2. Click anywhere outside the dropdown

**Expected Result:**
- Dropdown closes automatically

**Pass Criteria:** Dropdown closes on outside click

---

### 3. Logout Tests

#### Test 3.1: Sign Out Functionality
**Steps:**
1. Click user profile icon
2. Click "Sign Out" button
3. Observe behavior

**Expected Result:**
- Firebase sign-out called
- Django session cleared
- Redirects to login page (`/accounts/login/`)

**Pass Criteria:** User logged out and redirected

---

#### Test 3.2: Post-Logout Access
**Steps:**
1. Sign out (Test 3.1)
2. Try to navigate to `http://127.0.0.1:8000/`

**Expected Result:**
- Home page loads but without user authentication
- "Sign In" button appears in navigation

**Pass Criteria:** Unauthenticated state displayed

---

### 4. Backend API Tests

#### Test 4.1: Token Verification Endpoint
**Prerequisites:** Get Firebase ID token from browser console

**Steps:**
1. Open browser DevTools (F12)
2. Sign in and copy token from console
3. Test with curl:

```bash
curl -X POST http://127.0.0.1:8000/accounts/verify-token/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{"token": "YOUR_FIREBASE_TOKEN"}'
```

**Expected Result:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "test@example.com",
    "name": "Test User",
    "role": "teacher"
  }
}
```

**Pass Criteria:** Token verified and user info returned

---

#### Test 4.2: Invalid Token
**Steps:**
```bash
curl -X POST http://127.0.0.1:8000/accounts/verify-token/ \
  -H "Content-Type: application/json" \
  -d '{"token": "invalid_token"}'
```

**Expected Result:**
```json
{
  "error": "Invalid Firebase token"
}
```
Status code: 401

**Pass Criteria:** Invalid token rejected

---

#### Test 4.3: User Auto-Creation
**Prerequisites:** New Google account not in database

**Steps:**
1. Sign in with new Google account
2. Check Django admin or database

**Expected Result:**
- New User object created
- `firebase_uid` field populated
- Email, name fields populated from Firebase
- `role` set to TEACHER
- `school` set to None

**Pass Criteria:** User automatically created on first sign-in

---

### 5. Session Management Tests

#### Test 5.1: Session Persistence
**Steps:**
1. Sign in
2. Navigate to different pages
3. Refresh browser
4. Check if still signed in

**Expected Result:**
- User remains signed in across pages
- User remains signed in after refresh
- Session persists until expiry

**Pass Criteria:** Session persists correctly

---

#### Test 5.2: Session Expiry
**Prerequisites:** Set shorter session expiry for testing

**Steps:**
1. Sign in
2. Wait for session expiry (default: 1 hour)
3. Try to access protected page

**Expected Result:**
- Session expired
- User redirected to login (if middleware configured)
- Or shows unauthenticated state

**Pass Criteria:** Session expires after timeout

---

### 6. Security Tests

#### Test 6.1: CSRF Protection
**Steps:**
1. Try to call verify-token without CSRF token:

```bash
curl -X POST http://127.0.0.1:8000/accounts/verify-token/ \
  -H "Content-Type: application/json" \
  -d '{"token": "test"}'
```

**Expected Result:**
- 403 Forbidden error
- CSRF verification failed message

**Pass Criteria:** CSRF protection working

---

#### Test 6.2: XSS Protection
**Steps:**
1. Try to inject script in login form
2. Enter email: `<script>alert('XSS')</script>@test.com`
3. Submit form

**Expected Result:**
- Script not executed
- Firebase validation rejects invalid email
- No alert appears

**Pass Criteria:** XSS attempt blocked

---

## Browser Compatibility

Test in the following browsers:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Console Checks

### Expected Console Logs (Login)

```javascript
✅ Firebase initialized successfully
✅ Firebase connected
✅ Authentication successful: test@example.com
✅ Backend verification successful: {user: {...}}
```

### Expected Console Logs (Home Page)

```javascript
✅ User authenticated: test@example.com
```

### Expected Console Logs (Logout)

```javascript
// No specific logs, but no errors should appear
```

## Common Issues & Solutions

### Issue 1: Firebase Not Connecting
**Symptoms:** Red banner "Failed to connect to Firebase"
**Solutions:**
- Check internet connection
- Verify Firebase config in template
- Check Firebase Console for API key issues
- Check browser console for detailed errors

---

### Issue 2: Token Verification Fails
**Symptoms:** "Authentication failed on server" error
**Solutions:**
- Check Firebase service account credentials in `.env`
- Verify `FIREBASE_CONFIG` in `settings.py`
- Check Django logs: `logs/django.log`
- Ensure Firebase Admin SDK initialized

---

### Issue 3: Redirect Loop
**Symptoms:** Page keeps redirecting
**Solutions:**
- Clear browser cookies
- Check session configuration in `settings.py`
- Verify middleware order
- Check for JavaScript errors

---

### Issue 4: CSRF Token Missing
**Symptoms:** 403 Forbidden on verify-token
**Solutions:**
- Ensure Django CSRF cookie is set
- Check if CSRF token properly retrieved in JavaScript
- Verify `CSRF_TRUSTED_ORIGINS` in settings
- Try clearing cookies and reloading

---

## Performance Tests

### Load Time Tests
- Login page: < 2 seconds
- Firebase connection: < 1 second
- Sign-in process: < 3 seconds
- Home page load: < 2 seconds

### Concurrent Users
Test with multiple users signing in simultaneously:
- 10 users: Should work without issues
- 50 users: Monitor server performance
- 100+ users: Consider scaling

## Deployment Checklist

Before deploying to production:

### Configuration
- [ ] Update `ALLOWED_HOSTS` in settings
- [ ] Set `DEBUG=False`
- [ ] Configure `SECRET_KEY` (unique, secure)
- [ ] Set `CSRF_TRUSTED_ORIGINS` for your domain
- [ ] Enable HTTPS (`SECURE_SSL_REDIRECT=True`)
- [ ] Set secure cookie flags:
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`

### Firebase
- [ ] Verify Firebase production credentials
- [ ] Add production domain to Firebase authorized domains
- [ ] Configure Firebase security rules
- [ ] Enable Firebase Analytics (optional)

### Security
- [ ] Run `python manage.py check --deploy`
- [ ] Review security headers
- [ ] Set up rate limiting (optional)
- [ ] Configure CORS properly
- [ ] Set up monitoring/logging

### Testing
- [ ] All test cases pass
- [ ] No console errors
- [ ] Mobile responsiveness verified
- [ ] Cross-browser testing complete
- [ ] Load testing performed

## Monitoring

### Key Metrics to Monitor
1. **Authentication Success Rate**: > 95%
2. **Token Verification Latency**: < 500ms
3. **Session Creation Rate**: Track new users
4. **Error Rate**: < 1%
5. **API Response Time**: < 1 second

### Logs to Monitor
- Django logs: `logs/django.log`
- Firebase Authentication logs (Firebase Console)
- Server access logs
- Error tracking (Sentry, etc.)

## Support Contacts

For issues:
1. Check this testing guide
2. Review `FIREBASE_INTEGRATION.md`
3. Check Django logs
4. Review Firebase Console
5. Contact development team

## Revision History

- **Version 1.0** (2025-01-18): Initial testing guide
- Integration from demo files complete
- All test cases documented




























