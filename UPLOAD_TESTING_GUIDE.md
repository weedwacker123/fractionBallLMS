# File Upload Testing Guide

## ✅ Upload System is READY!

Your file upload system is now fully functional and stores files locally (no Firebase credentials needed for testing).

---

## 🚀 How to Upload Files

### Step 1: Make Sure You're Logged In

1. **Go to:** http://localhost:8000/accounts/login/
2. **Login with:**
   - Username: `admin`
   - Password: `admin123`

### Step 2: Go to Upload Page

**URL:** http://localhost:8000/upload/

You'll see a clean upload interface with:
- File type selector (Video or Resource)
- Drag-and-drop file upload area
- Title and description fields
- Grade level and topic selectors
- Big red "Upload File" button

### Step 3: Upload a File

1. **Select file type:**
   - Choose "Video" for MP4, MOV, AVI files (max 500MB)
   - Choose "Resource" for PDF, DOC, PPT, XLS files (max 50MB)

2. **Click "Upload a file"** or drag and drop

3. **Fill in the form:**
   - **Title** (required) - Auto-fills from filename
   - **Description** (optional)
   - **Grade Level** (optional) - K through 8
   - **Topic** (optional) - Fractions Basics, Equivalent Fractions, etc.

4. **Click "Upload File"**

5. **Success!** You'll see a green success message

---

## 📁 Where Files Are Stored

### Local Storage (Current Setup)

Files are saved to:
```
/Users/evantran/fractionBallLMS/media/
├── videos/          # Video files
├── resources/       # Resource files
├── thumbnails/      # Thumbnail images
└── lesson-plans/    # Lesson plan PDFs
```

Each file gets a unique ID to prevent naming conflicts.

### Database Records

Upload metadata is stored in SQLite database:
- **Videos**: `content_videoasset` table
- **Resources**: `content_resource` table

---

## 🔍 How to Verify Uploads Work

### Method 1: View in Web Interface

**Go to:** http://localhost:8000/my-uploads/

You'll see:
- ✅ All your uploaded videos
- ✅ All your uploaded resources
- ✅ File details (size, date, status)
- ✅ Edit and Delete buttons

### Method 2: Check Django Admin

1. **Go to:** http://localhost:8000/admin/
2. **Login** with admin credentials
3. **Navigate to:**
   - **Content → Video assets** - See all uploaded videos
   - **Content → Resources** - See all uploaded resources

You can:
- View all file details
- Edit metadata
- Delete files
- Change status (Draft → Published)

### Method 3: Check File System

```bash
# List uploaded videos
ls -lh /Users/evantran/fractionBallLMS/media/videos/

# List uploaded resources
ls -lh /Users/evantran/fractionBallLMS/media/resources/

# Check total storage used
du -sh /Users/evantran/fractionBallLMS/media/
```

### Method 4: Check Database

```bash
cd /Users/evantran/fractionBallLMS

# Count uploaded videos
python3 manage.py shell -c "from content.models import VideoAsset; print(f'Videos: {VideoAsset.objects.count()}')"

# Count uploaded resources
python3 manage.py shell -c "from content.models import Resource; print(f'Resources: {Resource.objects.count()}')"

# List recent uploads
python3 manage.py shell -c "
from content.models import VideoAsset
for v in VideoAsset.objects.order_by('-created_at')[:5]:
    print(f'- {v.title} ({v.file_size_formatted})')
"
```

---

## 📊 Supported File Types

### Videos
- **Formats:** MP4, MOV, AVI, MKV, WebM
- **Max Size:** 500 MB
- **MIME Types:** `video/mp4`, `video/quicktime`, `video/x-msvideo`, etc.

### Resources
- **Documents:** PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT
- **Images:** JPG, PNG, GIF, WebP
- **Max Size:** 50 MB

---

## 🧪 Quick Test Procedure

### Test Video Upload

1. Login: http://localhost:8000/accounts/login/
2. Upload: http://localhost:8000/upload/
3. Select "Video" type
4. Choose a small MP4 file (< 10MB for quick test)
5. Fill title: "Test Video Upload"
6. Select Grade: "5"
7. Select Topic: "Fractions Basics"
8. Click "Upload File"
9. ✅ You should see: "✅ Video 'Test Video Upload' uploaded successfully!"

### Verify Upload

1. Go to: http://localhost:8000/my-uploads/
2. ✅ You should see your video in the list
3. Check file size, date, status
4. Click "Edit" to modify details

### Test Resource Upload

1. Upload: http://localhost:8000/upload/
2. Select "Resource" type
3. Choose a PDF file
4. Fill title: "Test Resource"
5. Click "Upload File"
6. ✅ Success message appears
7. View at: http://localhost:8000/my-uploads/

---

## 🔄 Switching to Firebase Storage (Later)

Currently using **local storage** for easy testing. To switch to Firebase:

### Step 1: Get Complete Firebase Private Key

1. Go to: https://console.firebase.google.com/
2. Select project: **fractionball-lms**
3. Go to: Project Settings → Service Accounts
4. Click: "Generate new private key"
5. Download JSON file

### Step 2: Update .env File

Open `/Users/evantran/fractionBallLMS/.env` and update:

```bash
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
[PASTE FULL PRIVATE KEY HERE - SHOULD BE ~1700 CHARACTERS]
-----END PRIVATE KEY-----
"
```

**Important:** The private key must be complete, including:
- `-----BEGIN PRIVATE KEY-----`
- All the encoded key data (multiple lines)
- `-----END PRIVATE KEY-----`

### Step 3: Enable Firebase Storage

1. Firebase Console → **Storage**
2. Click "Get Started"
3. Choose location (e.g., `us-central1`)
4. Set security rules (see `FIREBASE_STORAGE_SETUP_GUIDE.md`)

### Step 4: Restart Server

```bash
pkill -f "manage.py runserver"
cd /Users/evantran/fractionBallLMS
python3 manage.py runserver 0.0.0.0:8000
```

### Step 5: Test

Upload should now save to Firebase Storage instead of local disk!

---

## 🛠️ Troubleshooting

### "Please login to upload"
**Solution:** Login first at http://localhost:8000/accounts/login/

### "File too large"
**Solution:** 
- Videos: Max 500MB
- Resources: Max 50MB
- Try a smaller file for testing

### "Upload failed"
**Solution:** Check server logs:
```bash
tail -50 /tmp/django_server.log
```

### Can't see uploads in "My Uploads"
**Solution:**
- Check Django admin: http://localhost:8000/admin/content/videoasset/
- Verify you're logged in as the same user who uploaded

### Files not in media folder
**Solution:**
```bash
# Check if media folder exists
ls -la /Users/evantran/fractionBallLMS/media/

# Check permissions
ls -ld /Users/evantran/fractionBallLMS/media/
```

---

## 📝 Upload Form Fields

### Required Fields
- ✅ **File** - The video or resource file
- ✅ **Title** - Descriptive name for the content

### Optional Fields
- **Description** - Detailed description
- **Grade Level** - K through 8
- **Topic** - Subject area
  - Fractions Basics
  - Equivalent Fractions
  - Comparing/Ordering
  - Number Line
  - Mixed ↔ Improper
  - Add/Subtract Fractions
  - Multiply/Divide Fractions
  - Decimals & Percents
  - Ratio/Proportion
  - Word Problems

---

## ✅ Testing Checklist

- [ ] Login successful
- [ ] Upload page loads (http://localhost:8000/upload/)
- [ ] Video upload works
- [ ] Resource upload works  
- [ ] Files appear in /media/ folder
- [ ] Uploads show in "My Uploads" page
- [ ] Uploads show in Django admin
- [ ] File metadata is correct
- [ ] Success messages appear
- [ ] Can edit uploaded files
- [ ] File sizes are calculated correctly

---

## 🎯 Next Steps After Testing

1. ✅ **Test local uploads** (current setup)
2. **Configure Firebase** (optional - for cloud storage)
3. **Add more content** (upload multiple files)
4. **Test different file types**
5. **Share uploads** (via Community page)
6. **Create playlists** (organize videos)

---

## 💡 Tips

- **Use small files for testing** (< 10MB) for faster uploads
- **Title auto-fills** from filename - you can edit it
- **Status starts as "DRAFT"** - change to "PUBLISHED" in admin
- **Local storage is perfect for development** - no internet needed
- **Switch to Firebase later** when you need cloud storage

---

## 🆘 Need Help?

**Server not running?**
```bash
cd /Users/evantran/fractionBallLMS
python3 manage.py runserver 0.0.0.0:8000
```

**Check if uploads are working:**
```bash
# View recent server activity
tail -30 /tmp/django_server.log
```

**Reset everything and start fresh:**
```bash
# Delete all uploads (keeps database)
rm -rf /Users/evantran/fractionBallLMS/media/videos/*
rm -rf /Users/evantran/fractionBallLMS/media/resources/*

# Or delete database too
rm /Users/evantran/fractionBallLMS/db.sqlite3
python3 manage.py migrate
python3 manage.py shell -c "from accounts.models import *; from django.contrib.auth import get_user_model; User = get_user_model(); school, _ = School.objects.get_or_create(domain='test-school', defaults={'name': 'Test School'}); User.objects.create_superuser(username='admin', email='admin@test.com', password='admin123', firebase_uid='test-admin', school=school, role='ADMIN')"
```

---

**Your upload system is ready! Go to http://localhost:8000/upload/ and start testing!** 🚀







