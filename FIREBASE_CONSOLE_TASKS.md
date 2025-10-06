# Firebase Console Configuration Tasks

## ✅ COMPLETED STEPS
- [x] Firebase project created (`fractionball-lms`)
- [x] Service account key generated and configured
- [x] Frontend Firebase configuration created
- [x] Environment variables configured
- [x] JavaScript authentication files created

## 🔥 REQUIRED FIREBASE CONSOLE TASKS

### 1. Enable Authentication Providers
**Location: Firebase Console → Authentication → Sign-in method**

#### Enable Email/Password:
1. Click on "Email/Password"
2. Toggle "Enable" to ON
3. Click "Save"

#### Enable Google Sign-In:
1. Click on "Google"
2. Toggle "Enable" to ON
3. **Project support email:** Use your email address
4. Click "Save"

### 2. Configure Firebase Storage
**Location: Firebase Console → Storage**

#### Initialize Storage:
1. Go to "Storage" in left sidebar
2. Click "Get started"
3. **Choose "Start in production mode"** (we have custom rules)
4. **Select location:** Choose closest to your users (e.g., us-central1)
5. Click "Done"

#### Update Storage Rules:
1. Go to "Storage" → "Rules" tab
2. **Replace the default rules** with:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow authenticated users to upload to their designated paths
    match /videos/{timePrefix}/{filename} {
      // Allow uploads via signed URLs (PUT requests)
      allow write: if request.auth != null 
        && request.method == 'put'
        && resource == null  // Only allow creation, not updates
        && request.resource.size <= 500 * 1024 * 1024  // 500MB limit
        && request.resource.contentType.matches('video/.*');
      
      // DENY direct download tokens for videos (streaming-only policy)
      allow read: if false;  // No direct downloads for videos
    }
    
    match /resources/{timePrefix}/{filename} {
      // Allow uploads via signed URLs
      allow write: if request.auth != null 
        && request.method == 'put'
        && resource == null
        && request.resource.size <= 50 * 1024 * 1024  // 50MB limit
        && (request.resource.contentType.matches('application/pdf')
            || request.resource.contentType.matches('application/.*word.*')
            || request.resource.contentType.matches('application/.*powerpoint.*')
            || request.resource.contentType.matches('application/.*excel.*')
            || request.resource.contentType.matches('application/.*spreadsheet.*')
            || request.resource.contentType.matches('text/plain')
            || request.resource.contentType.matches('image/.*'));
      
      // Allow reading resources with valid authentication
      allow read: if request.auth != null;
    }
    
    match /thumbnails/{timePrefix}/{filename} {
      // Allow thumbnail uploads
      allow write: if request.auth != null 
        && request.method == 'put'
        && resource == null
        && request.resource.size <= 10 * 1024 * 1024  // 10MB limit
        && request.resource.contentType.matches('image/.*');
      
      // Allow reading thumbnails
      allow read: if request.auth != null;
    }
    
    // Deny all other access
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```

3. Click "Publish"

### 3. Optional: Configure CORS for Storage
**Location: Google Cloud Console → Storage**

If you encounter CORS issues:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your `fractionball-lms` project
3. Go to Cloud Storage → Buckets
4. Find your Firebase storage bucket
5. Configure CORS if needed

### 4. Test Storage Rules (Optional)
**Location: Firebase Console → Storage → Rules**

1. Click "Rules Playground"
2. Test video upload: 
   - Operation: `create`
   - Path: `videos/20241006_120000/test.mp4`
   - Authenticated: ✅
3. Test video download (should fail):
   - Operation: `get` 
   - Path: `videos/20241006_120000/test.mp4`
   - Authenticated: ✅
   - Expected: ❌ DENY

## 🎯 NEXT STEPS AFTER FIREBASE CONSOLE SETUP

1. **Install npm dependencies:**
   ```bash
   npm install
   ```

2. **Test the Django application:**
   ```bash
   make up
   ```

3. **Verify Firebase integration:**
   - Go to `http://localhost:8000/api/healthz`
   - Should return 200 OK

4. **Test authentication:**
   - Go to `http://localhost:8000/upload/`
   - Try the authentication flow

## 🚨 IMPORTANT SECURITY NOTES

- ✅ Videos are streaming-only (no direct downloads)
- ✅ All operations require authentication
- ✅ File size limits enforced
- ✅ File type validation in place
- ✅ Service account keys are secure (not in client code)

## 📞 SUPPORT

If you encounter issues:
1. Check the Firebase Console logs
2. Verify authentication is working
3. Test storage rules in the playground
4. Check browser console for JavaScript errors

---
**Created:** $(date)
**Status:** Ready for Firebase Console configuration
