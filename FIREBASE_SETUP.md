# Firebase Setup Guide for Fraction Ball LMS

This guide covers the complete Firebase setup required for the Fraction Ball Teacher LMS platform.

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name: `fractionball-lms`
4. Enable Google Analytics (optional)
5. Complete project creation

## 2. Enable Authentication

1. In Firebase Console, go to **Authentication** > **Sign-in method**
2. Enable the following providers:
   - **Email/Password**: Enable
   - **Google**: Enable and configure OAuth consent screen

## 3. Setup Firebase Storage

### Enable Storage
1. Go to **Storage** in Firebase Console
2. Click "Get started"
3. Choose "Start in test mode" (we'll update rules later)
4. Select a location (choose closest to your users)

### Configure Storage Rules

Replace the default Storage rules with the following production-ready rules:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow authenticated users to upload to their designated paths
    match /videos/{timestamp}/{filename} {
      // Allow uploads via signed URLs (PUT requests)
      allow write: if request.auth != null 
        && request.method == 'put'
        && resource == null  // Only allow creation, not updates
        && request.resource.size <= 500 * 1024 * 1024  // 500MB limit
        && request.resource.contentType.matches('video/.*');
      
      // DENY direct download tokens for videos (streaming-only policy)
      allow read: if false;  // No direct downloads for videos
    }
    
    match /resources/{timestamp}/{filename} {
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
    
    match /thumbnails/{timestamp}/{filename} {
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

### Key Security Features:
- **Video Streaming Only**: Videos cannot be directly downloaded, only streamed
- **File Size Limits**: 500MB for videos, 50MB for resources
- **File Type Validation**: Only allowed MIME types can be uploaded
- **Authentication Required**: All operations require valid Firebase auth
- **Upload-Only Paths**: Prevents overwriting existing files

## 4. Configure CDN (Optional but Recommended)

For better video streaming performance:

1. Go to **Storage** > **Usage** tab
2. Note your default bucket URL
3. Consider setting up Firebase Hosting or Google Cloud CDN for better global performance

## 5. Generate Service Account Key

1. Go to **Project Settings** > **Service Accounts**
2. Click "Generate new private key"
3. Download the JSON file
4. **IMPORTANT**: Keep this file secure and never commit to version control

## 6. Update Environment Variables

Add the following to your `.env` file:

```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key-here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project.iam.gserviceaccount.com
```

## 7. Frontend Firebase Configuration

For the frontend authentication, you'll need to initialize Firebase in your web app:

```javascript
// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "your-sender-id",
  appId: "your-app-id"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

## 8. Storage Lifecycle Rules (Cost Optimization)

Set up lifecycle rules to automatically delete old files:

1. Go to **Storage** > **Rules**
2. Add lifecycle rules:
   - Delete uploaded files older than 90 days if not referenced in database
   - Move infrequently accessed files to coldline storage after 30 days

## 9. Monitoring and Alerts

Set up monitoring for:
- Storage usage
- Bandwidth usage
- Authentication failures
- Upload failures

## 10. Testing the Setup

1. Start your Django development server
2. Go to `/upload/` to test the upload UI
3. Try uploading a video and resource file
4. Verify files appear in Firebase Storage console
5. Check that videos stream but cannot be directly downloaded
6. Test resource downloads work with signed URLs

## Security Best Practices

1. **Never expose service account keys** in client-side code
2. **Use Firebase Auth Rules** to validate user permissions
3. **Implement rate limiting** on upload endpoints
4. **Monitor storage usage** to prevent abuse
5. **Regular security audits** of Storage rules
6. **Backup critical data** regularly

## Troubleshooting

### Common Issues:

1. **Upload fails with 403**: Check Storage rules and authentication
2. **File too large**: Verify size limits in rules and Django settings
3. **Invalid file type**: Check MIME type validation in rules
4. **Streaming not working**: Ensure public URLs are correctly generated

### Debug Mode:

Enable debug mode in Storage rules for testing:

```javascript
// Add this to rules for debugging (REMOVE in production)
allow read, write: if request.auth != null && resource.metadata.debug == 'true';
```

## Production Checklist

- [ ] Storage rules properly configured
- [ ] File size limits appropriate
- [ ] Video download prevention working
- [ ] Authentication properly integrated
- [ ] CDN configured for performance
- [ ] Lifecycle rules for cost optimization
- [ ] Monitoring and alerts set up
- [ ] Backup strategy implemented
- [ ] Security rules tested

---

**Important**: This setup ensures videos are streaming-only (cannot be downloaded) while resources can be downloaded with proper authentication, meeting the project requirements for content protection.
