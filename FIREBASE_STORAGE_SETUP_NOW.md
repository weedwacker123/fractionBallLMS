# Firebase Storage Setup - Quick Guide

## 🚨 Current Status

Your Firebase project is configured, but the **Storage bucket needs to be created**.

### What's Working
- ✅ Firebase credentials configured
- ✅ Service account: `firebase-adminsdk-fbsvc@fractionball-lms.iam.gserviceaccount.com`
- ✅ Project ID: `fractionball-lms`

### What's Missing
- ❌ Storage bucket: `fractionball-lms.appspot.com` doesn't exist yet

---

## 🔧 How to Fix This (5 Minutes)

### Option 1: Create Storage Bucket in Firebase Console (RECOMMENDED)

1. **Go to Firebase Console**
   - Visit: https://console.firebase.google.com/
   - Sign in with your Google account

2. **Select Your Project**
   - Click on project: `fractionball-lms`

3. **Navigate to Storage**
   - In the left sidebar, click **"Build"**
   - Click **"Storage"**

4. **Get Started**
   - Click the **"Get started"** button
   - Choose **"Start in production mode"** (we'll configure rules next)
   - Click **"Next"**

5. **Choose Location**
   - Select **"us-central1"** (or your preferred region)
   - Click **"Done"**

6. **Configure Security Rules**
   - Click the **"Rules"** tab at the top
   - Replace the default rules with:

```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow authenticated users to upload files
    match /{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null 
                   && request.resource.size < 500 * 1024 * 1024  // 500MB max
                   && (request.resource.contentType.matches('video/.*')
                       || request.resource.contentType.matches('application/pdf')
                       || request.resource.contentType.matches('image/.*'));
    }
    
    // Public read access for specific paths (optional)
    match /videos/{allPaths=**} {
      allow read: if true;
    }
    match /resources/{allPaths=**} {
      allow read: if true;
    }
  }
}
```

   - Click **"Publish"**

7. **Done!** 
   - Your storage bucket is now created and configured
   - The bucket name is: `fractionball-lms.appspot.com`

---

### Option 2: Use Default Firebase Storage Bucket Name

If you created a Firebase project but didn't set up Storage, the bucket might have a different name. Let's check:

1. Go to Firebase Console
2. Click on your project
3. Go to Project Settings (gear icon)
4. Scroll to "Your apps" section
5. Look for "Storage bucket" - it might show a different bucket name

If it shows a different bucket name, update your `.env` file:

```bash
FIREBASE_STORAGE_BUCKET=your-actual-bucket-name.appspot.com
```

---

## 🧪 Test Your Setup

After creating the bucket, restart your Django server and test:

```bash
# Stop the server (Ctrl+C)
# Then restart
cd /Users/evantran/fractionBallLMS
python3 manage.py shell -c "
from content.services import FirebaseStorageService
service = FirebaseStorageService()
if service.bucket:
    print('✅ Firebase Storage is working!')
    print(f'   Bucket: {service.bucket.name}')
else:
    print('❌ Firebase Storage still not working')
"
```

---

## 📤 Test File Upload

1. Go to: http://localhost:8000/upload/
2. Select a video or PDF file
3. Fill in the details
4. Click "Upload"
5. You should see: **"🔥 File uploaded to Firebase Cloud Storage!"**

---

## 🔄 How the Code Works Now

Your system has **automatic fallback**:

1. **Tries Firebase first**: If Firebase Storage is configured, files upload there
2. **Falls back to local storage**: If Firebase fails, files are stored locally in `/media/`

You can see which storage was used in the success message:
- Firebase: "🔥 File uploaded to Firebase Cloud Storage!"
- Local: "✅ File uploaded (local storage)"

---

## 🐛 Troubleshooting

### Issue: "The specified bucket does not exist"

**Solution**: You haven't created the Storage bucket yet. Follow Option 1 above.

### Issue: "Permission denied" or "403 Forbidden"

**Solutions**:
1. Check that your service account has the correct permissions:
   - Go to Firebase Console > Project Settings > Service Accounts
   - Make sure the service account has "Firebase Admin SDK" role
2. Check Storage Rules (see Option 1, step 6)

### Issue: "CORS error" when uploading from browser

**Solution**: Configure CORS in Firebase Storage:
1. Install Google Cloud SDK (already downloaded in your project)
2. Create a `cors.json` file:

```json
[
  {
    "origin": ["http://localhost:8000", "http://127.0.0.1:8000"],
    "method": ["GET", "HEAD", "PUT", "POST", "DELETE"],
    "maxAgeSeconds": 3600
  }
]
```

3. Apply CORS configuration:
```bash
gsutil cors set cors.json gs://fractionball-lms.appspot.com
```

---

## ✅ Next Steps

After setting up the bucket:

1. ✅ Create the Storage bucket (Option 1 above)
2. ✅ Configure security rules
3. ✅ Test with the command above
4. ✅ Try uploading a file through the website
5. ✅ Verify files appear in Firebase Console > Storage

---

## 📚 Additional Resources

- [Firebase Storage Documentation](https://firebase.google.com/docs/storage)
- [Security Rules Guide](https://firebase.google.com/docs/storage/security)
- [CORS Configuration](https://firebase.google.com/docs/storage/web/download-files#cors_configuration)

---

## 🎉 Once Complete

After setting up the bucket, **all your uploads will automatically go to Firebase Storage** instead of local storage!

- Videos and resources will be stored in the cloud
- Files will be accessible from anywhere
- You'll have Firebase's CDN for fast delivery
- No more local `/media/` folder clutter

















