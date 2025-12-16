# Firebase Storage Setup Guide

## Overview
This guide walks you through configuring Firebase Storage for the Fraction Ball LMS. Firebase Storage will host all video content, resources, lesson plans, and thumbnails.

## Prerequisites
- Firebase Console access (https://console.firebase.google.com/)
- Firebase project already created (`fractionball-lms`)
- Admin/Owner permissions on the Firebase project

---

## Step 1: Enable Firebase Storage

### 1.1 Navigate to Storage
1. Go to **Firebase Console**: https://console.firebase.google.com/
2. Select your project: **fractionball-lms**
3. Click on **Storage** in the left sidebar (under "Build" section)
4. Click **Get Started**

### 1.2 Choose Location
1. Select the default storage location (or choose based on your primary user base):
   - **Recommended**: `us-central1` (United States)
   - **Alternative**: Choose closest to your primary users
2. Click **Done**

Your Firebase Storage bucket will be created at:
```
gs://fractionball-lms.appspot.com
```

---

## Step 2: Configure Storage Security Rules

Firebase Storage uses security rules to control who can read, write, and delete files. These rules are critical for security.

### 2.1 Navigate to Rules
1. In Firebase Console > **Storage**
2. Click the **Rules** tab at the top

### 2.2 Update Security Rules
Replace the default rules with the following production-ready rules:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    
    // Helper function to check if user is authenticated
    function isSignedIn() {
      return request.auth != null;
    }
    
    // Helper function to check if user owns the file
    function isOwner(userId) {
      return request.auth.uid == userId;
    }
    
    // Videos folder: authenticated users can upload, anyone can read published videos
    match /videos/{timestamp}/{fileId} {
      // Allow authenticated users to upload videos
      allow create: if isSignedIn() 
                    && request.resource.size < 500 * 1024 * 1024  // 500 MB max
                    && request.resource.contentType.matches('video/.*');
      
      // Allow authenticated users to read videos
      allow read: if isSignedIn();
      
      // Allow uploader to delete their own videos
      allow delete: if isSignedIn() 
                    && resource.metadata.uploader == request.auth.uid;
    }
    
    // Resources folder: authenticated users can upload, anyone can read
    match /resources/{timestamp}/{fileId} {
      // Allow authenticated users to upload resources
      allow create: if isSignedIn() 
                    && request.resource.size < 50 * 1024 * 1024  // 50 MB max
                    && (request.resource.contentType.matches('application/pdf')
                        || request.resource.contentType.matches('application/.*word.*')
                        || request.resource.contentType.matches('application/.*excel.*')
                        || request.resource.contentType.matches('application/.*powerpoint.*')
                        || request.resource.contentType.matches('image/.*')
                        || request.resource.contentType.matches('text/.*'));
      
      // Allow authenticated users to read resources
      allow read: if isSignedIn();
      
      // Allow uploader to delete their own resources
      allow delete: if isSignedIn() 
                    && resource.metadata.uploader == request.auth.uid;
    }
    
    // Thumbnails folder: authenticated users can upload, anyone can read
    match /thumbnails/{timestamp}/{fileId} {
      // Allow authenticated users to upload thumbnails
      allow create: if isSignedIn() 
                    && request.resource.size < 10 * 1024 * 1024  // 10 MB max
                    && request.resource.contentType.matches('image/.*');
      
      // Allow authenticated users to read thumbnails
      allow read: if isSignedIn();
      
      // Allow uploader to delete their own thumbnails
      allow delete: if isSignedIn() 
                    && resource.metadata.uploader == request.auth.uid;
    }
    
    // Lesson plans folder: authenticated users can upload, anyone can read
    match /lesson-plans/{timestamp}/{fileId} {
      // Allow authenticated users to upload lesson plans
      allow create: if isSignedIn() 
                    && request.resource.size < 10 * 1024 * 1024  // 10 MB max
                    && request.resource.contentType == 'application/pdf';
      
      // Allow authenticated users to read lesson plans
      allow read: if isSignedIn();
      
      // Allow uploader to delete their own lesson plans
      allow delete: if isSignedIn() 
                    && resource.metadata.uploader == request.auth.uid;
    }
    
    // Deny everything else by default
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```

### 2.3 Publish Rules
1. Click **Publish** to apply the rules
2. Wait for confirmation message

---

## Step 3: Configure CORS for Web Access

CORS (Cross-Origin Resource Sharing) allows your web application to access Firebase Storage from your domain.

### 3.1 Install Google Cloud SDK (if not already installed)
```bash
# macOS (using Homebrew)
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### 3.2 Authenticate with Google Cloud
```bash
gcloud auth login
```

### 3.3 Set Your Project
```bash
gcloud config set project fractionball-lms
```

### 3.4 Create CORS Configuration File
Create a file named `cors.json` in your project root:

```json
[
  {
    "origin": ["*"],
    "method": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "responseHeader": ["Content-Type", "x-goog-meta-uploader"],
    "maxAgeSeconds": 3600
  }
]
```

**Production Note**: Replace `"*"` with your specific domains:
```json
"origin": ["https://yourdomain.com", "http://localhost:3000"]
```

### 3.5 Apply CORS Configuration
```bash
gsutil cors set cors.json gs://fractionball-lms.appspot.com
```

### 3.6 Verify CORS Configuration
```bash
gsutil cors get gs://fractionball-lms.appspot.com
```

---

## Step 4: Set Up Lifecycle Management (Optional but Recommended)

Lifecycle rules automatically delete temporary or old files to save costs.

### 4.1 Create Lifecycle Configuration
Create a file named `lifecycle.json`:

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 30,
          "matchesPrefix": ["temp/"]
        }
      },
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 90,
          "matchesPrefix": ["videos/", "resources/"],
          "numNewerVersions": 1
        }
      }
    ]
  }
}
```

This configuration:
- Deletes files in `temp/` folder after 30 days
- Keeps only the most recent version of videos/resources (older versions deleted after 90 days)

### 4.2 Apply Lifecycle Rules
```bash
gsutil lifecycle set lifecycle.json gs://fractionball-lms.appspot.com
```

### 4.3 Verify Lifecycle Rules
```bash
gsutil lifecycle get gs://fractionball-lms.appspot.com
```

---

## Step 5: Configure Storage Quotas and Monitoring

### 5.1 Set Up Budget Alerts
1. Go to **Firebase Console** > **Project Settings** (gear icon)
2. Click **Usage and billing** tab
3. Click **Details & Settings** under Firebase plan
4. Click **Set budget alerts**
5. Set budget threshold (e.g., $50/month)
6. Add your email for alerts

### 5.2 Enable Storage Metrics
1. In Firebase Console > **Storage**
2. Click **Usage** tab
3. Monitor:
   - **Storage usage**: Total GB stored
   - **Downloads**: Bandwidth usage
   - **Uploads**: Number of files uploaded

---

## Step 6: Test Firebase Storage Integration

### 6.1 Install Python Dependencies
```bash
cd /Users/evantran/fractionBallLMS
pip install google-cloud-storage==2.10.0 pillow==10.1.0 python-magic==0.4.27
```

### 6.2 Run Django Server
```bash
python manage.py runserver
```

### 6.3 Test Upload Endpoint
```bash
# Request upload URL
curl -X POST http://localhost:8000/api/content/storage/uploads/request-upload/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_type": "video",
    "content_type": "video/mp4",
    "file_size": 10485760,
    "file_name": "test-video.mp4"
  }'
```

Expected response:
```json
{
  "upload_url": "https://storage.googleapis.com/...",
  "file_path": "videos/20250118/abc123.mp4",
  "file_id": "temp-abc123",
  "expires_in": 3600
}
```

### 6.4 Upload File to Signed URL
```bash
# Upload a test video file
curl -X PUT "UPLOAD_URL_FROM_ABOVE" \
  -H "Content-Type: video/mp4" \
  --upload-file /path/to/test-video.mp4
```

### 6.5 Confirm Upload
```bash
curl -X POST http://localhost:8000/api/content/storage/uploads/confirm-upload/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_path": "videos/20250118/abc123.mp4",
    "file_type": "video",
    "title": "Test Video",
    "description": "This is a test video"
  }'
```

---

## Step 7: Production Checklist

Before going to production, verify:

### Security
- [ ] Storage rules are properly configured and tested
- [ ] CORS is restricted to your production domains only
- [ ] File size limits are enforced in rules
- [ ] Only authenticated users can upload/download

### Performance
- [ ] CDN is enabled for Firebase Storage
- [ ] Signed URLs are used for all file access
- [ ] Lifecycle rules are configured to delete old/temp files

### Monitoring
- [ ] Budget alerts are set up
- [ ] Storage usage monitoring is enabled
- [ ] Error logging is configured for failed uploads

### Backup
- [ ] Consider setting up Cloud Storage Transfer Service for backups
- [ ] Document your backup/restore procedures

---

## Troubleshooting

### Issue: "Permission denied" when uploading
**Solution**: Check Firebase Storage rules. Ensure user is authenticated and file meets size/type requirements.

### Issue: CORS errors in browser
**Solution**: 
1. Verify CORS configuration with `gsutil cors get gs://fractionball-lms.appspot.com`
2. Ensure your domain is in the allowed origins
3. Clear browser cache and retry

### Issue: Files not accessible after upload
**Solution**:
1. Check if file exists: Use Firebase Console > Storage > Files tab
2. Verify storage rules allow read access
3. Check if signed URL has expired (default 1 hour)

### Issue: Upload fails with size error
**Solution**:
1. Check file size limits in storage rules
2. Verify `file_size` parameter in upload request
3. Adjust limits if needed for your use case

---

## Additional Resources

- **Firebase Storage Documentation**: https://firebase.google.com/docs/storage
- **Security Rules Reference**: https://firebase.google.com/docs/rules/rules-language
- **CORS Configuration Guide**: https://cloud.google.com/storage/docs/configuring-cors
- **Python Client Library**: https://googleapis.dev/python/storage/latest/index.html

---

## Support

For issues specific to this integration:
1. Check Django logs: `logs/django.log`
2. Check Firebase Console > Storage > Usage for errors
3. Review storage rules simulator in Firebase Console

## Next Steps

After completing this setup:
1. Create a test upload through your Django admin panel
2. Verify files appear in Firebase Console > Storage
3. Test download URLs and streaming
4. Configure your frontend to use the upload/download endpoints
5. Set up monitoring and alerts for production use












