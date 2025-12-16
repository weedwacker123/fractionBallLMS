# Firebase Storage Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing and testing the Firebase Storage integration in your Django application.

---

## Part 1: Installation and Setup

### 1.1 Install Python Dependencies

```bash
cd /Users/evantran/fractionBallLMS
pip install google-cloud-storage==2.10.0 pillow==10.1.0 python-magic==0.4.27
```

### 1.2 Verify Firebase Configuration

Check that your Firebase credentials are properly configured in `fractionball/settings.py`:

```python
# Firebase Admin SDK Configuration
FIREBASE_CONFIG = {
    'type': os.getenv('FIREBASE_TYPE', 'service_account'),
    'project_id': os.getenv('FIREBASE_PROJECT_ID', 'fractionball-lms'),
    'private_key_id': os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    'private_key': os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
    'client_email': os.getenv('FIREBASE_CLIENT_EMAIL'),
    'client_id': os.getenv('FIREBASE_CLIENT_ID'),
    'auth_uri': os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
    'token_uri': os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
    'auth_provider_x509_cert_url': os.getenv('FIREBASE_AUTH_PROVIDER_CERT_URL'),
    'client_x509_cert_url': os.getenv('FIREBASE_CLIENT_CERT_URL'),
}
```

### 1.3 Update Environment Variables

Add to your `.env` file:

```env
# Firebase Configuration (from Firebase Console > Project Settings > Service Accounts)
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=fractionball-lms
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour\nPrivate\nKey\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@fractionball-lms.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40fractionball-lms.iam.gserviceaccount.com
```

---

## Part 2: API Endpoints Reference

### 2.1 Request Upload URL

**Endpoint**: `POST /api/content/storage/uploads/request-upload/`

**Description**: Generate a signed URL for client-side file upload

**Request Body**:
```json
{
    "file_type": "video",
    "content_type": "video/mp4",
    "file_size": 52428800,
    "file_name": "my-video.mp4"
}
```

**Parameters**:
- `file_type` (string, required): One of: `video`, `resource`, `thumbnail`, `lesson`
- `content_type` (string, required): MIME type (e.g., `video/mp4`, `application/pdf`)
- `file_size` (integer, required): File size in bytes
- `file_name` (string, optional): Original file name

**Response** (200 OK):
```json
{
    "upload_url": "https://storage.googleapis.com/fractionball-lms.appspot.com/videos/20250118/abc123.mp4?...",
    "file_path": "videos/20250118/abc123.mp4",
    "file_id": "temp-abc123",
    "expires_in": 3600,
    "instructions": {
        "method": "PUT",
        "headers": {
            "Content-Type": "video/mp4"
        }
    }
}
```

### 2.2 Upload File to Signed URL

**Endpoint**: `PUT {upload_url}` (from previous response)

**Description**: Upload the actual file to Firebase Storage

**Headers**:
```
Content-Type: video/mp4  (must match the content_type from step 2.1)
```

**Body**: Raw file binary data

**cURL Example**:
```bash
curl -X PUT "https://storage.googleapis.com/..." \
  -H "Content-Type: video/mp4" \
  --upload-file /path/to/video.mp4
```

**JavaScript Example**:
```javascript
const file = document.getElementById('fileInput').files[0];

// 1. Request upload URL
const response = await fetch('/api/content/storage/uploads/request-upload/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({
        file_type: 'video',
        content_type: file.type,
        file_size: file.size,
        file_name: file.name
    })
});

const data = await response.json();

// 2. Upload file to signed URL
const uploadResponse = await fetch(data.upload_url, {
    method: 'PUT',
    headers: {
        'Content-Type': file.type
    },
    body: file
});

if (uploadResponse.ok) {
    console.log('File uploaded successfully!');
}
```

### 2.3 Confirm Upload

**Endpoint**: `POST /api/content/storage/uploads/confirm-upload/`

**Description**: Create database record after successful upload

**Request Body**:
```json
{
    "file_path": "videos/20250118/abc123.mp4",
    "file_type": "video",
    "title": "Introduction to Fractions",
    "description": "A basic introduction to fractions"
}
```

**Response** (201 Created):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Introduction to Fractions",
    "description": "A basic introduction to fractions",
    "storage_uri": "videos/20250118/abc123.mp4",
    "file_size": 52428800,
    "grade": "K",
    "topic": "fractions_basics",
    "status": "DRAFT",
    "created_at": "2025-01-18T10:30:00Z",
    "owner": {
        "id": 1,
        "email": "teacher@example.com"
    }
}
```

### 2.4 Get Streaming URL

**Endpoint**: `GET /api/content/storage/videos/{video_id}/stream/`

**Description**: Get a signed streaming URL for a video

**Response** (200 OK):
```json
{
    "streaming_url": "https://storage.googleapis.com/...",
    "expires_in": 3600,
    "video_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Introduction to Fractions"
}
```

### 2.5 Get Resource Download URL

**Endpoint**: `GET /api/content/storage/resources/{resource_id}/download/`

**Description**: Get a signed download URL for a resource

**Response** (200 OK):
```json
{
    "download_url": "https://storage.googleapis.com/...",
    "expires_in": 3600,
    "resource_id": "660e8400-e29b-41d4-a716-446655440000",
    "file_name": "Lesson Plan",
    "file_type": "pdf"
}
```

### 2.6 Delete File

**Endpoint**: `DELETE /api/content/storage/uploads/delete-file/`

**Description**: Delete a file from Firebase Storage

**Request Body**:
```json
{
    "file_path": "videos/20250118/abc123.mp4"
}
```

**Response** (200 OK):
```json
{
    "message": "File deleted successfully"
}
```

---

## Part 3: Frontend Integration Example

### 3.1 HTML File Upload Form

```html
<!DOCTYPE html>
<html>
<head>
    <title>Upload Video</title>
</head>
<body>
    <h1>Upload Video</h1>
    
    <form id="uploadForm">
        <label for="title">Title:</label>
        <input type="text" id="title" required><br><br>
        
        <label for="description">Description:</label>
        <textarea id="description"></textarea><br><br>
        
        <label for="videoFile">Video File:</label>
        <input type="file" id="videoFile" accept="video/*" required><br><br>
        
        <button type="submit">Upload</button>
    </form>
    
    <div id="progress" style="display:none;">
        <p>Uploading... <span id="progressPercent">0</span>%</p>
        <progress id="progressBar" max="100" value="0"></progress>
    </div>
    
    <div id="result"></div>
    
    <script src="/static/js/upload.js"></script>
</body>
</html>
```

### 3.2 JavaScript Upload Handler

```javascript
// /static/js/upload.js

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const fileInput = document.getElementById('videoFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    // Show progress
    document.getElementById('progress').style.display = 'block';
    document.getElementById('result').innerHTML = '';
    
    try {
        // Step 1: Request upload URL
        const response1 = await fetch('/api/content/storage/uploads/request-upload/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include',
            body: JSON.stringify({
                file_type: 'video',
                content_type: file.type,
                file_size: file.size,
                file_name: file.name
            })
        });
        
        if (!response1.ok) {
            const error = await response1.json();
            throw new Error(error.error || 'Failed to get upload URL');
        }
        
        const data1 = await response1.json();
        console.log('Upload URL received:', data1.file_path);
        
        // Step 2: Upload file to signed URL
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                document.getElementById('progressPercent').textContent = percent;
                document.getElementById('progressBar').value = percent;
            }
        });
        
        xhr.addEventListener('load', async function() {
            if (xhr.status === 200) {
                console.log('File uploaded to Firebase Storage');
                
                // Step 3: Confirm upload and create database record
                try {
                    const response3 = await fetch('/api/content/storage/uploads/confirm-upload/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        credentials: 'include',
                        body: JSON.stringify({
                            file_path: data1.file_path,
                            file_type: 'video',
                            title: title,
                            description: description
                        })
                    });
                    
                    if (!response3.ok) {
                        const error = await response3.json();
                        throw new Error(error.error || 'Failed to confirm upload');
                    }
                    
                    const video = await response3.json();
                    console.log('Video created:', video);
                    
                    document.getElementById('result').innerHTML = 
                        `<p style="color: green;">✅ Video uploaded successfully!</p>
                         <p>Video ID: ${video.id}</p>
                         <p>Title: ${video.title}</p>`;
                    
                    // Reset form
                    document.getElementById('uploadForm').reset();
                    document.getElementById('progress').style.display = 'none';
                    
                } catch (error) {
                    console.error('Confirm error:', error);
                    document.getElementById('result').innerHTML = 
                        `<p style="color: red;">❌ Error: ${error.message}</p>`;
                }
                
            } else {
                throw new Error(`Upload failed with status ${xhr.status}`);
            }
        });
        
        xhr.addEventListener('error', function() {
            document.getElementById('result').innerHTML = 
                '<p style="color: red;">❌ Upload failed</p>';
        });
        
        xhr.open('PUT', data1.upload_url);
        xhr.setRequestHeader('Content-Type', file.type);
        xhr.send(file);
        
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('result').innerHTML = 
            `<p style="color: red;">❌ Error: ${error.message}</p>`;
        document.getElementById('progress').style.display = 'none';
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

---

## Part 4: Testing

### 4.1 Test Video Upload (cURL)

```bash
# 1. Request upload URL
curl -X POST http://localhost:8000/api/content/storage/uploads/request-upload/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "file_type": "video",
    "content_type": "video/mp4",
    "file_size": 10485760,
    "file_name": "test-video.mp4"
  }'

# Save the upload_url and file_path from response

# 2. Upload file
curl -X PUT "UPLOAD_URL_FROM_STEP_1" \
  -H "Content-Type: video/mp4" \
  --upload-file /path/to/test-video.mp4

# 3. Confirm upload
curl -X POST http://localhost:8000/api/content/storage/uploads/confirm-upload/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "file_path": "FILE_PATH_FROM_STEP_1",
    "file_type": "video",
    "title": "Test Video",
    "description": "This is a test video"
  }'
```

### 4.2 Test Video Streaming

```bash
# Get streaming URL for a video
curl -X GET http://localhost:8000/api/content/storage/videos/VIDEO_ID/stream/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# Use the streaming_url from response in your video player
```

### 4.3 Test Resource Upload

```bash
# 1. Request upload URL for PDF
curl -X POST http://localhost:8000/api/content/storage/uploads/request-upload/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "file_type": "resource",
    "content_type": "application/pdf",
    "file_size": 1048576,
    "file_name": "lesson-plan.pdf"
  }'

# 2. Upload file
curl -X PUT "UPLOAD_URL" \
  -H "Content-Type: application/pdf" \
  --upload-file /path/to/lesson-plan.pdf

# 3. Confirm upload
curl -X POST http://localhost:8000/api/content/storage/uploads/confirm-upload/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "file_path": "FILE_PATH",
    "file_type": "resource",
    "title": "Lesson Plan",
    "description": "Test lesson plan"
  }'
```

---

## Part 5: File Size and Type Limits

### Video Files
- **Max Size**: 500 MB
- **Allowed Types**: 
  - `video/mp4`
  - `video/quicktime`
  - `video/x-msvideo`
  - `video/x-matroska`
  - `video/webm`

### Resource Files
- **Max Size**: 50 MB
- **Allowed Types**:
  - PDF: `application/pdf`
  - Word: `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - PowerPoint: `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`
  - Excel: `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
  - Text: `text/plain`

### Thumbnail Files
- **Max Size**: 10 MB
- **Allowed Types**: `image/jpeg`, `image/png`, `image/webp`, `image/gif`

### Lesson Plan Files
- **Max Size**: 10 MB
- **Allowed Types**: `application/pdf`

---

## Part 6: Rate Limits

### Upload Limits
- **Per Hour**: 50 uploads per user
- **Per Day**: 200 uploads per user

### Storage Quota
- **Per User**: 10 GB total storage

---

## Part 7: Security Features

### File Validation
- ✅ File type verification (MIME type)
- ✅ File size limits
- ✅ File name sanitization
- ✅ Extension blacklist (prevents .exe, .bat, etc.)
- ✅ Content type verification

### Access Control
- ✅ Authentication required for all operations
- ✅ Firebase Storage security rules
- ✅ Signed URLs with expiration (1 hour default)
- ✅ User ownership validation

### Rate Limiting
- ✅ Upload frequency limits
- ✅ Storage quota per user
- ✅ File size limits per type

---

## Part 8: Troubleshooting

### Error: "Permission denied" when uploading
**Cause**: Firebase Storage rules reject the upload
**Solution**:
1. Check Firebase Console > Storage > Rules
2. Verify user is authenticated
3. Check file size and type limits

### Error: "CORS error" in browser
**Cause**: CORS not configured properly
**Solution**:
1. Follow CORS setup in `FIREBASE_STORAGE_SETUP_GUIDE.md`
2. Verify your domain is in allowed origins
3. Clear browser cache

### Error: "File not found" after upload
**Cause**: Upload succeeded but file doesn't exist in storage
**Solution**:
1. Check Firebase Console > Storage > Files tab
2. Verify `file_path` is correct
3. Wait a few seconds for replication

### Error: "Token expired"
**Cause**: Signed URL expired (default 1 hour)
**Solution**: Request a new upload URL

---

## Part 9: Production Deployment Checklist

Before deploying to production:

### Firebase Configuration
- [ ] Firebase Storage is enabled
- [ ] Security rules are configured and tested
- [ ] CORS is set to specific domains (not `*`)
- [ ] Lifecycle rules are configured
- [ ] Budget alerts are set up

### Application Configuration
- [ ] All environment variables are set
- [ ] Dependencies are installed
- [ ] Database migrations are run
- [ ] Static files are collected
- [ ] Error logging is configured

### Security
- [ ] File validation is enabled
- [ ] Rate limiting is configured
- [ ] Signed URLs are used for all access
- [ ] User authentication is required
- [ ] HTTPS is enforced

### Monitoring
- [ ] Storage usage monitoring
- [ ] Upload error tracking
- [ ] Rate limit monitoring
- [ ] Cost alerts are configured

---

## Support

For implementation issues:
1. Check Django logs: `logs/django.log`
2. Check Firebase Console > Storage > Usage
3. Review security rules in Firebase Console
4. Test endpoints with cURL first
5. Check browser console for frontend errors

























