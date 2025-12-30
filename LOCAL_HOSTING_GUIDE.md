# Local Hosting Guide - Fraction Ball LMS

## 🚀 Quick Start

### Starting the Server

```bash
# Navigate to project directory
cd /Users/evantran/fractionBallLMS

# Start Django development server
python3 manage.py runserver
```

The server will start on: **http://localhost:8000**

You should see output like:
```
Django version 4.2.7, using settings 'fractionball.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

---

## 🌐 Accessing Your Website

Once the server is running, open your browser and visit:

| Page | URL | Description |
|------|-----|-------------|
| **Homepage** | http://localhost:8000/ | Main landing page with activities |
| **Login** | http://localhost:8000/accounts/django-login/ | Django admin login |
| **Upload** | http://localhost:8000/upload/ | Upload videos and resources |
| **My Uploads** | http://localhost:8000/my-uploads/ | View all your uploads |
| **Admin Panel** | http://localhost:8000/admin/ | Full admin dashboard |
| **Library** | http://localhost:8000/library/ | Browse content library |
| **Community** | http://localhost:8000/community/ | Community page |

---

## 🔑 Login Credentials

**Username:** `admin`  
**Password:** `admin123`

Use these credentials for:
- Django Login Page (http://localhost:8000/accounts/django-login/)
- Admin Panel (http://localhost:8000/admin/)

---

## ⏸️ Stopping the Server

To stop the server:

1. Go to the terminal where the server is running
2. Press: **CONTROL + C** (or **CMD + C** on Mac)

You'll see:
```
^C
Quit the server.
```

---

## 🔄 Restarting the Server

If you need to restart the server (after code changes):

```bash
# Stop the server first (CONTROL-C)
# Then start it again
python3 manage.py runserver
```

**Note:** Most code changes auto-reload, but some changes (like settings.py) require a manual restart.

---

## 🐛 Troubleshooting

### Port Already in Use

If you see: `Error: That port is already in use.`

```bash
# Find and kill the process on port 8000
lsof -i :8000
# Note the PID number, then:
kill -9 <PID>

# Or use a different port
python3 manage.py runserver 8001
```

### Module Not Found Errors

If you see `ModuleNotFoundError`:

```bash
# Reinstall dependencies
python3 -m pip install -r requirements.txt
```

### Database Errors

If you see database-related errors:

```bash
# Run migrations
python3 manage.py migrate

# If that doesn't work, recreate the database
rm db.sqlite3
python3 manage.py migrate
python3 manage.py createsuperuser
```

---

## 📁 Project Structure

```
/Users/evantran/fractionBallLMS/
├── manage.py           # Django management script
├── db.sqlite3          # Local database
├── media/              # Uploaded files stored here
│   ├── videos/
│   ├── resources/
│   └── thumbnails/
├── static/             # Static files (CSS, JS)
├── templates/          # HTML templates
├── accounts/           # User authentication
├── content/            # Content management
└── fractionball/       # Main project settings
```

---

## 🎯 Typical Workflow

1. **Start Server**
   ```bash
   cd /Users/evantran/fractionBallLMS
   python3 manage.py runserver
   ```

2. **Login**
   - Visit: http://localhost:8000/accounts/django-login/
   - Username: `admin`
   - Password: `admin123`

3. **Upload Content**
   - Visit: http://localhost:8000/upload/
   - Select file (video or PDF)
   - Fill in title, grade, topic, standards
   - Click "Upload"

4. **View Uploads**
   - Visit: http://localhost:8000/my-uploads/
   - See all your uploaded content
   - Edit or delete as needed

5. **Admin Panel** (for advanced management)
   - Visit: http://localhost:8000/admin/
   - Manage users, content, permissions

---

## 🔧 Advanced Commands

### Run Database Migrations
```bash
python3 manage.py migrate
```

### Create a New Admin User
```bash
python3 manage.py createsuperuser
```

### Collect Static Files (for production)
```bash
python3 manage.py collectstatic
```

### Run on a Different Port
```bash
python3 manage.py runserver 8080
```

### Run on All Network Interfaces (accessible from other devices)
```bash
python3 manage.py runserver 0.0.0.0:8000
```

---

## 📊 System Requirements

- **Python:** 3.12.0 (installed)
- **Database:** SQLite3 (included with Python)
- **Storage:** Local filesystem (`media/` directory)
- **OS:** macOS (Darwin 23.6.0)

---

## ✅ Current Status

✅ **Server Status:** Running on http://localhost:8000  
✅ **Database:** SQLite3 configured and migrated  
✅ **Admin User:** Created (admin/admin123)  
✅ **File Uploads:** Local storage configured  
✅ **Templates:** All pages styled with Tailwind CSS  
✅ **Authentication:** Django authentication working  

---

## 🆘 Need Help?

If you encounter any issues:

1. Check the terminal output for error messages
2. Visit the troubleshooting section above
3. Make sure you're in the correct directory
4. Ensure all dependencies are installed
5. Check that port 8000 is available

---

## 🎉 You're All Set!

Your local hosting environment is ready to use. Simply run:

```bash
python3 manage.py runserver
```

Then visit: **http://localhost:8000**

Happy coding! 🚀






























