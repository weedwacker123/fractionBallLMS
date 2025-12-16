# Firebase Storage Integration - Quick Start

## 🎯 What's Been Implemented

A complete Firebase Storage integration for handling video and resource uploads with:

✅ **Backend API** - Django REST Framework endpoints for upload/download
✅ **Security** - File validation, rate limiting, and access control
✅ **Storage Service** - Firebase Storage wrapper with signed URLs
✅ **Database Models** - Updated VideoAsset and Resource models
✅ **Documentation** - Comprehensive setup and implementation guides

---

## 📦 What You Need to Do

### 1. Install Python Dependencies (5 minutes)

```bash
cd /Users/evantran/fractionBallLMS
pip install google-cloud-storage==2.10.0 pillow==10.1.0 python-magic==0.4.27
```

### 2. Configure Firebase Console (30-45 minutes)

Follow the detailed guide: **`FIREBASE_STORAGE_SETUP_GUIDE.md`**

**Key Steps**:
1. **Enable Firebase Storage** in Firebase Console
2. **Configure Security Rules** - Copy rules from guide
3. **Set up CORS** - Allow your domain to access storage
4. **Configure Lifecycle Rules** - Auto-delete old files (optional)
5. **Set Budget Alerts** - Monitor costs

### 3. Test the Integration (15 minutes)

Follow the test examples in: **`FIREBASE_STORAGE_IMPLEMENTATION_GUIDE.md`**

**Quick Test**:
```bash
# Start Django server
python manage.py runserver

# Test upload (see guide for full cURL commands)
curl -X POST http://localhost:8000/api/content/storage/uploads/request-upload/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{"file_type": "video", "content_type": "video/mp4", "file_size": 10485760, "file_name": "test.mp4"}'
```

---

## 📚 Documentation Files

### Primary Guides

1. **`FIREBASE_STORAGE_SETUP_GUIDE.md`** ⭐
   - Firebase Console configuration
   - Security rules setup
   - CORS configuration
   - Lifecycle management
   - **START HERE for Firebase setup**

2. **`FIREBASE_STORAGE_IMPLEMENTATION_GUIDE.md`** ⭐
   - API endpoint reference
   - Frontend integration examples
   - Testing instructions
   - Troubleshooting guide
   - **USE THIS for implementation**

3. **`FIREBASE_STORAGE_QUICK_START.md`** (this file)
   - High-level overview
   - Quick reference

### Code Files

- **`content/firebase_storage.py`** - Storage service module
- **`content/upload_views.py`** - Upload/download API endpoints
- **`content/upload_urls.py`** - URL routing
- **`content/file_validators.py`** - Security and validation
- **`content/models.py`** - Updated with Firebase methods

---

## 🔑 Key API Endpoints

All endpoints are under: `/api/content/storage/`

### Upload Flow
```
1. POST   /uploads/request-upload/    → Get signed upload URL
2. PUT    {signed_url}                → Upload file to Firebase
3. POST   /uploads/confirm-upload/    → Create database record
```

### Access Flow
```
GET   /videos/{id}/stream/           → Get video streaming URL
GET   /resources/{id}/download/      → Get resource download URL
```

### Management
```
DELETE  /uploads/delete-file/        → Delete file from storage
```

---

## 🛡️ Security Features

✅ **Authentication Required** - All endpoints require login
✅ **File Type Validation** - Only allowed MIME types accepted
✅ **File Size Limits** - 500MB for videos, 50MB for resources
✅ **Rate Limiting** - 50 uploads/hour, 200/day per user
✅ **Storage Quotas** - 10GB per user
✅ **Signed URLs** - All access uses expiring signed URLs (1 hour)
✅ **Firebase Security Rules** - Server-side enforcement

---

## 📊 File Limits

| File Type | Max Size | Allowed Formats |
|-----------|----------|-----------------|
| Video | 500 MB | MP4, MOV, AVI, MKV, WebM |
| Resource | 50 MB | PDF, Word, Excel, PowerPoint, Images |
| Thumbnail | 10 MB | JPEG, PNG, WebP, GIF |
| Lesson Plan | 10 MB | PDF only |

---

## 🚀 Production Deployment

### Before Going Live:

1. **Firebase Console**
   - [ ] Enable Firebase Storage
   - [ ] Configure security rules
   - [ ] Set CORS to your domain only (not `*`)
   - [ ] Enable lifecycle rules
   - [ ] Set up budget alerts

2. **Environment Variables**
   - [ ] All Firebase credentials in `.env`
   - [ ] `FIREBASE_PROJECT_ID` set correctly
   - [ ] Private key properly formatted

3. **Testing**
   - [ ] Test video upload end-to-end
   - [ ] Test resource upload
   - [ ] Test streaming URLs
   - [ ] Verify security rules block unauthorized access
   - [ ] Test rate limiting

4. **Monitoring**
   - [ ] Set up error logging
   - [ ] Configure storage usage alerts
   - [ ] Monitor upload success/failure rates

---

## 💡 Usage Examples

### Python/Django
```python
from content.firebase_storage import get_storage_service

# Generate upload URL
storage = get_storage_service()
upload_url, file_path = storage.generate_upload_url(
    file_type='video',
    content_type='video/mp4',
    file_size=52428800,
    user_id=request.user.id
)

# Generate streaming URL
video = VideoAsset.objects.get(id=video_id)
streaming_url = video.get_streaming_url(expiration_minutes=60)
```

### JavaScript
```javascript
// Upload a file
async function uploadVideo(file) {
    // 1. Request upload URL
    const response = await fetch('/api/content/storage/uploads/request-upload/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            file_type: 'video',
            content_type: file.type,
            file_size: file.size,
            file_name: file.name
        })
    });
    
    const data = await response.json();
    
    // 2. Upload to signed URL
    await fetch(data.upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file
    });
    
    // 3. Confirm upload
    await fetch('/api/content/storage/uploads/confirm-upload/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            file_path: data.file_path,
            file_type: 'video',
            title: 'My Video',
            description: 'Description here'
        })
    });
}
```

---

## ❓ FAQ

### Q: Do I need to change my existing code?
**A**: If you're starting fresh, no. If you have existing upload code, you'll need to migrate to the new endpoints.

### Q: Where are files stored?
**A**: Files are stored in Firebase Storage at `gs://fractionball-lms.appspot.com`

### Q: How long do signed URLs last?
**A**: Default is 1 hour. Configurable per request.

### Q: What happens if a user uploads a malicious file?
**A**: Multiple layers of protection:
1. File type validation (MIME type)
2. Extension blacklist
3. Firebase security rules
4. File size limits

### Q: How much will Firebase Storage cost?
**A**: Firebase Storage pricing (as of 2025):
- **Storage**: $0.026/GB/month
- **Download**: $0.12/GB
- **Upload**: Free
- **Operations**: $0.05/10,000 operations

**Estimate for 100 videos (50GB)**:
- Storage: ~$1.30/month
- Downloads (10GB/month): ~$1.20/month
- **Total**: ~$2.50/month

### Q: Can I use this for local development?
**A**: Yes! Just point to your Firebase project. Files will be stored in the cloud even during development.

---

## 🆘 Need Help?

1. **Setup Issues**: See `FIREBASE_STORAGE_SETUP_GUIDE.md`
2. **Implementation Questions**: See `FIREBASE_STORAGE_IMPLEMENTATION_GUIDE.md`
3. **API Reference**: See Part 2 of implementation guide
4. **Error Messages**: Check Django logs (`logs/django.log`)
5. **Firebase Console**: Check Storage > Usage tab for errors

---

## 📝 Next Steps

1. **Install dependencies** (command above)
2. **Read `FIREBASE_STORAGE_SETUP_GUIDE.md`** for Firebase Console setup
3. **Configure Firebase Storage** (follow guide steps)
4. **Test with cURL** (examples in implementation guide)
5. **Integrate with your frontend** (examples provided)
6. **Deploy to production** (use checklist above)

---

## ✅ Integration Checklist

- [ ] Python dependencies installed
- [ ] Firebase Storage enabled in console
- [ ] Security rules configured and published
- [ ] CORS configured
- [ ] Environment variables set
- [ ] Tested upload endpoint
- [ ] Tested streaming endpoint
- [ ] Frontend integrated (if applicable)
- [ ] Production deployment checklist complete
- [ ] Monitoring and alerts configured

---

**Questions or issues?** Check the comprehensive guides or review the code comments in the implementation files.

























